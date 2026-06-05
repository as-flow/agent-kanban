# Hammerspoon Ghostty Hotkey Integration

This guide describes how to use Hammerspoon to focus all Ghostty windows with a single global hotkey on macOS.

## Why Hammerspoon

Ghostty can run multiple terminal windows as separate app instances. macOS menu automation such as `Bring All to Front` may only raise some of those windows. Hammerspoon can enumerate every running Ghostty instance by bundle ID and raise each window through the macOS Accessibility APIs.

## Install Hammerspoon

Install Hammerspoon with Homebrew:

```sh
brew install --cask hammerspoon
```

Launch Hammerspoon once:

```sh
open -a Hammerspoon
```

Grant Hammerspoon Accessibility access in:

```text
System Settings -> Privacy & Security -> Accessibility
```

## Configure the Hotkey

Create or edit `~/.hammerspoon/init.lua`:

```lua
local ghosttyBundleID = "com.mitchellh.ghostty"

hs.ipc.cliInstall()

local function raiseGhosttyWindows()
  local apps = hs.application.applicationsForBundleID(ghosttyBundleID)

  if #apps == 0 then
    hs.application.launchOrFocusByBundleID(ghosttyBundleID)
    return
  end

  for _, app in ipairs(apps) do
    app:activate(true)

    for _, window in ipairs(app:allWindows()) do
      if window:isMinimized() then
        window:unminimize()
      end

      window:raise()
    end
  end
end

local function focusGhosttyWindows()
  raiseGhosttyWindows()
  hs.timer.doAfter(0.15, raiseGhosttyWindows)
  hs.timer.doAfter(0.35, raiseGhosttyWindows)
end

hs.hotkey.bind({ "ctrl", "alt", "cmd" }, "G", focusGhosttyWindows)

hs.autoLaunch(true)
hs.alert.show("Ghostty hotkey loaded: Ctrl+Option+Cmd+G")
```

The repeated raise passes are intentional. On some Ghostty setups, a single pass raises only one or two windows because macOS processes each app instance asynchronously.

## Reload and Test

Reload the config from Hammerspoon:

```text
Hammerspoon -> File -> Reload Config
```

Then press:

```text
Control + Option + Command + G
```

All visible Ghostty windows should move to the front. If the shortcut does not work, confirm that Hammerspoon is running and has Accessibility permission.
