# Roblox Plugin API - create.roblox.com Reference

Source: https://create.roblox.com/docs/reference/engine/classes/Plugin

## Class: Plugin

**Inheritance:** Instance > Object

The `Plugin` class is the primary interface for creating Studio extensions, including custom widgets, toolbars, buttons, and contextual menus.

### Key Characteristics
- **NotCreatable**: Cannot be instantiated directly
- **Access**: Available via `Global.RobloxGlobals.plugin` in plugin scripts
- **Memory Category**: Instances
- **Security**: Most methods require PluginSecurity

---

## Properties

| Property | Type | Access | Description |
|----------|------|--------|-------------|
| `CollisionEnabled` | boolean | ReadOnly | Returns whether Studio's Collisions toolbar option is enabled |
| `DisableUIDragDetectorDrags` | boolean | Read/Write | Controls UI drag detector behavior |
| `GridSize` | float | ReadOnly | Current grid snapping size (may have rounding errors) |
| `IsDebuggable` | boolean | Read/Write | Debuggability state |

---

## Methods

### Activation & State Management

**`Activate(exclusiveMouse: boolean)`**
- Activates the plugin with optional exclusive mouse control
- Only one plugin can be active at a time
- Related events: `Deactivation`, `Unloading`

**`Deactivate()`**
- Deactivates the plugin and disengages PluginMouse

**`IsActivated(): boolean`**
- Returns activation state

**`IsActivatedWithExclusiveMouse(): boolean`**
- Returns true if active with exclusive mouse access

---

### Widget & UI Creation

**`CreateDockWidgetPluginGuiAsync(pluginGuiId: string, dockWidgetPluginGuiInfo: DockWidgetPluginGuiInfo): DockWidgetPluginGui`** [Yields]
- Creates a dockable widget window
- `pluginGuiId`: Unique identifier for state persistence
- Replaces deprecated `CreateDockWidgetPluginGui()`

**Example:**
```lua
local widgetInfo = DockWidgetPluginGuiInfo.new(
    Enum.InitialDockState.Float, true, false, 200, 300, 150, 150
)
local widget = plugin:CreateDockWidgetPluginGuiAsync("TestWidget", widgetInfo)
```

**`CreateToolbar(name: string): PluginToolbar`**
- Creates a toolbar for plugin buttons

**`CreatePluginAction(actionId: string, text: string, statusTip: string, iconName: string, allowBinding: boolean): PluginAction`**
- Creates a performable action without direct toolbar association
- Returns `PluginAction` object with `Triggered` event

**`CreatePluginMenu(id: string, title: string, icon: string): PluginMenu`**
- Creates context menu with `PluginAction` support
- Supports submenus and separators

---

### Input & Selection

**`GetMouse(): PluginMouse`**
- Returns mouse object when plugin is active with exclusive mouse

**`GetSelectedRibbonTool(): RibbonTool`**
- Returns currently selected Studio tool

**`SelectRibbonTool(tool: RibbonTool, position: UDim2)`**
- Activates specified Studio tool

**`GetJoinMode(): JointCreationMode`**
- Returns joint creation mode from toolbar

---

### Settings & Storage

**`GetSetting(key: string): Variant`**
- Retrieves persistent plugin setting
- Returns nil if key doesn't exist
- Note: May silently fail with multiple plugin instances

**`SetSetting(key: string, value: Variant)`**
- Stores persistent setting (survives Studio restart)
- JSON format with restrictions on backslashes, newlines, quotes, periods in keys
- May silently fail with concurrent instances

**Example:**
```lua
local RAN_BEFORE_KEY = "RunBefore"
if plugin:GetSetting(RAN_BEFORE_KEY) then
    print("Welcome back!")
else
    plugin:SetSetting(RAN_BEFORE_KEY, true)
    print("First run!")
end
```

---

### Scripting & Documentation

**`OpenScript(script: LuaSourceContainer, lineNumber: int = 1)`** [Deprecated]
- Opens script in editor at specified line

**`OpenWikiPage(url: string)`**
- Opens context help to specified wiki page
- Example: `plugin:OpenWikiPage("API:Class/BasePart")`

**`GetStudioUserId(): int64`** [Deprecated]
- Returns logged-in user's ID or 0

---

### Asset Management

**`PromptForExistingAssetIdAsync(assetType: string): int64`** [Yields]
- Prompts user to select asset by type
- Returns asset ID or -1 if cancelled

**`PromptSaveSelectionAsync(suggestedFileName: string): boolean`** [Yields]
- Prompts user to save current selection
- Returns true if file was saved

**`SaveSelectedToRoblox()`**
- Opens upload window for current selection

---

### FBX Import (Animation/Rigging)

**`ImportFbxAnimationAsync(rigModel: Instance, isR15: boolean = true): Instance`** [Yields]
- Imports .fbx animation onto rig
- Creates KeyframeSequence in Workspace

**`ImportFbxRigAsync(isR15: boolean = true): Instance`** [Yields]
- Imports .fbx file as character rig with meshes

---

### CSG Operations

**`Union(objects: Instances): UnionOperation`**
- Unions parts and returns operation

**`Intersect(objects: Instances): IntersectOperation`**
- Intersects parts and returns operation

**`Negate(objects: Instances): Instances`**
- Negates parts and returns operations

**`Separate(objects: Instances): Instances`**
- Separates UnionOperations into constituent parts

---

### Drag & Drop

**`StartDrag(dragData: Dictionary)`**
- Initiates drag operation with parameters:
  - `Sender` (string): Identifies drag source
  - `MimeType` (string): Data format
  - `Data` (string): Drag content
  - `MouseIcon` (Content): Cursor icon
  - `DragIcon` (Content): Drag visual
  - `HotSpot` (Vector2): Icon offset from cursor

**Related Events:**
- `PluginDragEntered`
- `PluginDragMoved`
- `PluginDragDropped`
- `PluginDragLeft`

---

## Events

**`Plugin.Deactivation`**
- Fires when plugin loses active state
- Triggered by `Deactivate()` or another plugin's `Activate()`

**`Plugin.Unloading`**
- Fires immediately before plugin stops running
- Occurs on disable, uninstall, update, or place close
- Use for cleanup (plugin instances auto-cleanup)

---

## Security & Capabilities

- **PluginSecurity**: Required for most plugin methods
- **RobloxScriptSecurity**: Certain properties like `DisableUIDragDetectorDrags`
- **CapabilityControl**: Required for sandboxing/capabilities features

---

## Related Classes

- `DockWidgetPluginGui`: Dockable UI container
- `PluginToolbar`: Toolbar container
- `PluginAction`: Named performable action
- `PluginMenu`: Context menu
- `PluginMouse`: Input object when active

---

## Notes

- Module scripts don't receive plugin reference; pass explicitly from main script
- Widget state persists via `pluginGuiId`
- Settings use JSON; avoid special characters in keys
- Only one plugin activation at a time; others receive `Deactivation`
