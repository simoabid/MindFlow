# MindFlow — Project Context & Debug History

Hey, I'm SeeMoo. I built this project called **MindFlow** — a system-wide AI-powered autocomplete for Linux. It's an IBus input method engine that uses Google Gemini to predict what you're about to type. You type anywhere, predictions show up in a candidate bar, you press Tab to accept. Works on Wayland, no root needed.

The project is at `~/Documents/Projects/mindflow/`. Everything is built and working — the Gemini API client, the prediction engine with caching and debouncing, the config system, unit tests, integration tests, install/uninstall scripts, README, the whole thing. **The only problem is the last mile: getting the IBus daemon to actually create and use our engine.**

## What MindFlow Does

The flow is simple:
```
User types → IBus intercepts keystrokes → MindFlow buffers context
→ Sends to Gemini API → Shows predictions in IBus candidate bar
→ Tab inserts the prediction into whatever app you're using
```

The engine class (`MindFlowEngine`) extends `IBus.Engine`, handles keystrokes in `do_process_key_event`, manages a preedit buffer, triggers predictions in background threads, and displays them via `update_auxiliary_text`. It's all working — I verified the Gemini pipeline end-to-end with real API calls and it returns good predictions.

## The System

- Zorin OS 18.1 (Ubuntu 24.04 base)
- GNOME 46, Wayland session
- Python 3.12 (venv with `--system-site-packages` for `gi` module)
- IBus 1.5.29
- Gemini model: `gemini-3.1-flash-lite-preview`

## What Works

- `mindflow/gemini_client.py` — Gemini API wrapper, tested with real key
- `mindflow/predictor.py` — caching, debouncing, thread-safe
- `mindflow/config.py` — dataclass config at `~/.config/mindflow/config.json`
- `mindflow/constants.py` — all app constants
- `mindflow/engine.py` — the IBus engine (keystroke handling, preedit, predictions)
- 16/16 unit tests pass (mocked API)
- Integration test passes 4/4 with real Gemini API
- `install.sh` / `uninstall.sh` — working
- Component XML installed at `~/.local/share/ibus/component/mindflow.xml` and `/usr/share/ibus/component/mindflow.xml`
- `ibus list-engine | grep mind` shows `mindflow - MindFlow AI Autocomplete`
- GNOME input sources has `('ibus', 'mindflow')` registered via gsettings
- Launcher at `~/.local/share/mindflow/mindflow-engine` sets `IBUS_ADDRESS` from `~/.config/ibus/bus/*` and runs the engine

## The Problem

When I run `ibus engine mindflow`, it times out:
```
IBUS-WARNING: ibus_bus_call_sync: org.freedesktop.IBus.SetGlobalEngine:
GDBus.Error:org.freedesktop.DBus.Error.Failed: Set global engine failed: Timeout was reached
```

The daemon DOES spawn the engine process — I can see it in `ps aux`. The engine process DOES connect to the IBus private D-Bus bus — I verified this with `ss -xp` showing a socket to `/home/seemoo/.cache/ibus/dbus-*`. The engine registers its component and enters `IBus.main()`. But the daemon never successfully creates an engine instance.

## What I've Tried

### 1. Factory Object Path Issue

I discovered that `IBus.Factory.new(bus.get_connection())` doesn't set the `object_path`. The Python override in `/usr/lib/python3/dist-packages/gi/overrides/IBus.py` only sets it when you pass `bus=`:

```python
class Factory(IBus.Factory):
    def __init__(self, bus=None, **kwargs):
        if bus is not None:
            kwargs.setdefault('connection', bus.get_connection())
            kwargs.setdefault('object_path', IBus.PATH_FACTORY)
        super(Factory, self).__init__(**kwargs)
```

I switched to `IBus.Factory(bus=bus)`. After this, the factory IS at `/org/freedesktop/IBus/Factory` — I confirmed via D-Bus introspection that the `CreateEngine` method is exposed.

### 2. `add_engine` with GType vs Class

I was using `factory.add_engine(ENGINE_NAME, MindFlowEngine.__gtype__)`. The problem is that `MindFlowEngine.__gtype__` is a GType object, which is NOT callable. The Python `do_create_engine` tries to call `engine_type()` to create instances, which fails.

I switched to `factory.add_engine(ENGINE_NAME, MindFlowEngine)` (passing the class). After this, local `factory.create_engine("mindflow")` works and returns a proper instance.

**But neither of these fixed the D-Bus issue.** The daemon still can't create engines via D-Bus.

### 3. `license_` Parameter

`IBus.Component` and `IBus.EngineDesc` don't support `license_` as a parameter. I removed it. This fixed a crash but wasn't the main issue.

### 4. IBUS_ADDRESS Not Set

When the daemon spawns the engine process, `IBUS_ADDRESS` wasn't in the environment. The engine was connecting to the session bus instead of the IBus private bus. I updated the launcher script to read `IBUS_ADDRESS` from `~/.config/ibus/bus/*` and export it. After this, the engine connects to the correct bus.

### 5. Subclassing IBus.Factory

I tried subclassing `IBus.Factory` to override `do_create_engine`:

```python
class MindFlowFactory(IBus.Factory):
    def __init__(self, bus):
        super().__init__(bus=bus)
    
    def do_create_engine(self, engine_name):
        if engine_name == ENGINE_NAME:
            return MindFlowEngine()
        return None
```

**With `__gtype_name__`** — segfault. The GObject type system tries to register a new type and fails.

**Without `__gtype_name__`** — no segfault. The factory creates fine. AND `do_create_engine` IS actually called when CreateEngine is invoked via D-Bus — I confirmed this with logging.

### 6. The Object Path Assertion

When `do_create_engine` returns a `MindFlowEngine` instance, the daemon crashes with:
```
IBUS:ERROR:ibusfactory.c:276:ibus_factory_service_method_call: assertion failed: (object_path != NULL)
```

Looking at the IBus C source, after `do_create_engine` returns, the C code calls `ibus_factory_register_engine(factory, engine)` which registers the engine on D-Bus and gives it an object path. When we override `do_create_engine` in Python, this C post-processing doesn't happen.

### 7. `engine.register(connection, path)`

I tried calling `engine.register(connection, path)` inside `do_create_engine` to manually register the engine on D-Bus:

```python
def do_create_engine(self, engine_name):
    if engine_name == ENGINE_NAME:
        engine = MindFlowEngine()
        path = f"/org/freedesktop/IBus/Engine/MindFlow/1"
        engine.register(connection, path)
        return engine
    return None
```

First attempt: `engine.register()` with no args gave `IBus.Service.register() takes exactly 2 arguments (1 given)`.

Second attempt with `engine.register(connection, path)`: the process produced NO output at all and the D-Bus call still hung. The `register()` call seems to block or crash silently.

### 8. Monkey-patching `do_create_engine` on instance

I tried monkey-patching `factory.do_create_engine = my_func` on a factory instance. The function was never called — GObject virtual methods go through the vtable, not Python attribute lookup.

## Current State of engine.py

Right now the code uses the non-subclassed approach:
```python
factory = IBus.Factory(bus=bus)
factory.add_engine(ENGINE_NAME, MindFlowEngine)
bus.register_component(component)
IBus.main()
```

This doesn't work because the C-level factory handler doesn't find the engine type in its hash table. The `add_engine` call only updates the Python-level `_engines` dict, not the C-level `engine_table`.

## Key Files

| File | What it does |
|------|-------------|
| `mindflow/engine.py` | Engine class, factory, main() |
| `mindflow/gemini_client.py` | Gemini API wrapper |
| `mindflow/predictor.py` | Caching + debouncing |
| `mindflow/config.py` | Config dataclass |
| `mindflow/constants.py` | Constants |
| `data/mindflow.xml` | IBus component descriptor |
| `data/mindflow-engine.xml` | Engine metadata |
| `~/.local/share/mindflow/mindflow-engine` | Launcher script |
| `~/.config/mindflow/config.json` | Config (has API key) |
| `~/.local/share/ibus/component/mindflow.xml` | Installed component XML |
| `/usr/share/ibus/component/mindflow.xml` | System component XML |
| `/usr/lib/python3/dist-packages/gi/overrides/IBus.py` | IBus Python overrides |

## How I Test

```bash
pkill -9 -f mindflow; pkill -9 ibus-daemon; sleep 1
ibus-daemon -drx; sleep 2
ibus list-engine | grep mind          # Shows: mindflow - MindFlow AI Autocomplete
ibus engine mindflow                  # THIS IS WHERE IT FAILS (timeout)
```

## D-Bus Introspection of Our Factory

When the engine process is running, I introspected its factory:
```xml
<interface name="org.freedesktop.IBus.Factory">
    <method name="CreateEngine">
        <arg type="s" name="name" direction="in"/>
        <arg type="o" name="arg_1" direction="out"/>
    </method>
</interface>
```

The method IS exposed. The daemon CAN see it. But calling it either hangs (non-subclassed) or crashes with assertion failure (subclassed without proper engine registration).

## IBus Version Info

```
IBus 1.5.29
gir1.2-ibus-1.0 1.5.29-2
python3-ibus-1.0 1.5.29-2
```

The IBus Python overrides are at `/usr/lib/python3/dist-packages/gi/overrides/IBus.py`.

---

That's everything I know. The project is 99% done. The Gemini pipeline works, the engine handles keystrokes, everything is wired up. The only thing broken is the handshake between the IBus daemon and our engine process — specifically, the daemon calling `CreateEngine` on our factory and getting back a properly registered engine object.
