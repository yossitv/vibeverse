local HttpService = game:GetService("HttpService")
local ChangeHistoryService = game:GetService("ChangeHistoryService")
local Selection = game:GetService("Selection")

local SETTINGS = {
	BASE_URL = "base_url",
	LAST_JOB_ID = "last_job_id",
	LAST_PROMPT = "last_prompt",
}

local DEFAULT_BASE_URL = "http://127.0.0.1:8000"
local POLL_INTERVAL_SECONDS = 1.0
local TERMINAL_STATES = {
	exported = true,
	placed = true,
	failed = true,
}

local function getSetting(key, fallback)
	local ok, value = pcall(function()
		return plugin:GetSetting(key)
	end)
	if ok and value ~= nil then
		return value
	end
	return fallback
end

local function setSetting(key, value)
	pcall(function()
		plugin:SetSetting(key, value)
	end)
end

local function trim(value)
	return (value or ""):match("^%s*(.-)%s*$")
end

local function normalizeBaseUrl(value)
	local normalized = trim(value)
	normalized = normalized:gsub("/+$", "")
	if normalized == "" then
		return DEFAULT_BASE_URL
	end
	return normalized
end

local function decodeJson(body)
	if not body or body == "" then
		return nil
	end
	local ok, decoded = pcall(function()
		return HttpService:JSONDecode(body)
	end)
	if ok then
		return decoded
	end
	return nil
end

local function requestJson(method, baseUrl, path, payload)
	local headers = {
		["Content-Type"] = "application/json",
	}
	local request = {
		Url = baseUrl .. path,
		Method = method,
		Headers = headers,
	}

	if payload ~= nil then
		request.Body = HttpService:JSONEncode(payload)
	end

	local response = HttpService:RequestAsync(request)
	local decoded = decodeJson(response.Body)
	if response.Success then
		return decoded or {}
	end

	local errorMessage = response.StatusMessage or ("HTTP " .. tostring(response.StatusCode))
	if type(decoded) == "table" and type(decoded.error) == "string" then
		errorMessage = decoded.error
	end
	error(errorMessage)
end

local function createCorner(parent, radius)
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, radius)
	corner.Parent = parent
end

local function createPadding(parent, left, right, top, bottom)
	local padding = Instance.new("UIPadding")
	padding.PaddingLeft = UDim.new(0, left)
	padding.PaddingRight = UDim.new(0, right)
	padding.PaddingTop = UDim.new(0, top)
	padding.PaddingBottom = UDim.new(0, bottom)
	padding.Parent = parent
end

local function createSection(parent, title)
	local section = Instance.new("Frame")
	section.Name = title:gsub("%s+", "") .. "Section"
	section.BackgroundColor3 = Color3.fromRGB(34, 37, 46)
	section.BorderSizePixel = 0
	section.AutomaticSize = Enum.AutomaticSize.Y
	section.Size = UDim2.new(1, 0, 0, 0)
	section.Parent = parent
	createCorner(section, 10)
	createPadding(section, 12, 12, 12, 12)

	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, 8)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = section

	local label = Instance.new("TextLabel")
	label.Name = "SectionTitle"
	label.BackgroundTransparency = 1
	label.Size = UDim2.new(1, 0, 0, 18)
	label.Font = Enum.Font.GothamSemibold
	label.Text = title
	label.TextColor3 = Color3.fromRGB(240, 242, 247)
	label.TextSize = 14
	label.TextXAlignment = Enum.TextXAlignment.Left
	label.Parent = section

	return section
end

local function createLabel(parent, name, text, size, color)
	local label = Instance.new("TextLabel")
	label.Name = name
	label.BackgroundTransparency = 1
	label.AutomaticSize = Enum.AutomaticSize.Y
	label.Size = UDim2.new(1, 0, 0, size or 18)
	label.Font = Enum.Font.Gotham
	label.Text = text or ""
	label.TextColor3 = color or Color3.fromRGB(213, 217, 226)
	label.TextSize = size or 13
	label.TextWrapped = true
	label.TextXAlignment = Enum.TextXAlignment.Left
	label.TextYAlignment = Enum.TextYAlignment.Top
	label.Parent = parent
	return label
end

local function createButton(parent, name, text, color)
	local button = Instance.new("TextButton")
	button.Name = name
	button.AutoButtonColor = true
	button.BackgroundColor3 = color
	button.BorderSizePixel = 0
	button.Font = Enum.Font.GothamSemibold
	button.Size = UDim2.new(0, 0, 0, 32)
	button.AutomaticSize = Enum.AutomaticSize.X
	button.Text = text
	button.TextColor3 = Color3.fromRGB(255, 255, 255)
	button.TextSize = 13
	button.Parent = parent
	createCorner(button, 8)
	createPadding(button, 12, 12, 0, 0)
	return button
end

local function setButtonEnabled(button, enabled, activeColor)
	button.Active = enabled
	button.AutoButtonColor = enabled
	button.TextTransparency = enabled and 0 or 0.35
	button.BackgroundColor3 = enabled and activeColor or Color3.fromRGB(75, 78, 88)
end

local function createInfoLine(parent, title)
	local frame = Instance.new("Frame")
	frame.Name = title:gsub("%s+", "") .. "Row"
	frame.BackgroundTransparency = 1
	frame.Size = UDim2.new(1, 0, 0, 20)
	frame.Parent = parent

	local key = Instance.new("TextLabel")
	key.BackgroundTransparency = 1
	key.Size = UDim2.new(0, 110, 1, 0)
	key.Font = Enum.Font.GothamSemibold
	key.Text = title
	key.TextColor3 = Color3.fromRGB(152, 158, 173)
	key.TextSize = 12
	key.TextXAlignment = Enum.TextXAlignment.Left
	key.Parent = frame

	local value = Instance.new("TextLabel")
	value.Name = "Value"
	value.BackgroundTransparency = 1
	value.Position = UDim2.new(0, 110, 0, 0)
	value.Size = UDim2.new(1, -110, 1, 0)
	value.Font = Enum.Font.Gotham
	value.Text = "-"
	value.TextColor3 = Color3.fromRGB(235, 238, 244)
	value.TextSize = 12
	value.TextTruncate = Enum.TextTruncate.AtEnd
	value.TextXAlignment = Enum.TextXAlignment.Left
	value.Parent = frame

	return value
end

local toolbar = plugin:CreateToolbar("VibeVerse")
local toggleButton = toolbar:CreateButton(
	"OpenVibeVerse",
	"Open the VibeVerse asset agent",
	"rbxassetid://4458901886"
)
toggleButton.ClickableWhenViewportHidden = true

local widgetInfo = DockWidgetPluginGuiInfo.new(
	Enum.InitialDockState.Right,
	false,
	false,
	420,
	640,
	320,
	420
)

local widgetFactory = plugin.CreateDockWidgetPluginGuiAsync or plugin.CreateDockWidgetPluginGui
local widget = widgetFactory(plugin, "VibeVerseDockWidget", widgetInfo)
widget.Title = "VibeVerse"
widget.ZIndexBehavior = Enum.ZIndexBehavior.Sibling

local root = Instance.new("ScrollingFrame")
root.Name = "Root"
root.Active = true
root.AutomaticCanvasSize = Enum.AutomaticSize.None
root.BackgroundColor3 = Color3.fromRGB(20, 22, 28)
root.BorderSizePixel = 0
root.CanvasSize = UDim2.new(0, 0, 0, 0)
root.ScrollBarImageColor3 = Color3.fromRGB(82, 91, 111)
root.ScrollBarThickness = 6
root.ScrollingDirection = Enum.ScrollingDirection.Y
root.Size = UDim2.fromScale(1, 1)
root.Parent = widget

local rootLayout = Instance.new("UIListLayout")
rootLayout.Padding = UDim.new(0, 10)
rootLayout.SortOrder = Enum.SortOrder.LayoutOrder
rootLayout.Parent = root

createPadding(root, 12, 12, 12, 12)

local hero = Instance.new("Frame")
hero.Name = "Hero"
hero.BackgroundColor3 = Color3.fromRGB(28, 34, 48)
hero.BorderSizePixel = 0
hero.AutomaticSize = Enum.AutomaticSize.Y
hero.Size = UDim2.new(1, 0, 0, 0)
hero.Parent = root
createCorner(hero, 12)
createPadding(hero, 12, 12, 12, 12)

local heroLayout = Instance.new("UIListLayout")
heroLayout.Padding = UDim.new(0, 4)
heroLayout.SortOrder = Enum.SortOrder.LayoutOrder
heroLayout.Parent = hero

local heroTitle = createLabel(hero, "Title", "Cursor for Game Crafting", 16, Color3.fromRGB(245, 247, 252))
heroTitle.Font = Enum.Font.GothamBold
createLabel(hero, "Subtitle", "Chat with the asset pipeline, poll backend jobs, and place the exported result into Studio.", 12, Color3.fromRGB(176, 184, 201))

local backendSection = createSection(root, "Backend")
createLabel(backendSection, "BackendHint", "Point the plugin at the local backend API started by `python3 -m backend.api.server`.", 12, Color3.fromRGB(176, 184, 201))

local urlRow = Instance.new("Frame")
urlRow.Name = "UrlRow"
urlRow.BackgroundTransparency = 1
urlRow.Size = UDim2.new(1, 0, 0, 32)
urlRow.Parent = backendSection

local urlBox = Instance.new("TextBox")
urlBox.Name = "BaseUrlBox"
urlBox.BackgroundColor3 = Color3.fromRGB(24, 27, 34)
urlBox.BorderSizePixel = 0
urlBox.ClearTextOnFocus = false
urlBox.Font = Enum.Font.Code
urlBox.PlaceholderText = DEFAULT_BASE_URL
urlBox.Size = UDim2.new(1, -86, 1, 0)
urlBox.Text = normalizeBaseUrl(getSetting(SETTINGS.BASE_URL, DEFAULT_BASE_URL))
urlBox.TextColor3 = Color3.fromRGB(235, 238, 244)
urlBox.TextSize = 13
urlBox.TextXAlignment = Enum.TextXAlignment.Left
urlBox.Parent = urlRow
createCorner(urlBox, 8)
createPadding(urlBox, 10, 10, 0, 0)

local saveUrlButton = Instance.new("TextButton")
saveUrlButton.Name = "SaveUrlButton"
saveUrlButton.AutoButtonColor = true
saveUrlButton.BackgroundColor3 = Color3.fromRGB(76, 110, 245)
saveUrlButton.BorderSizePixel = 0
saveUrlButton.Font = Enum.Font.GothamSemibold
saveUrlButton.Position = UDim2.new(1, -78, 0, 0)
saveUrlButton.Size = UDim2.new(0, 78, 1, 0)
saveUrlButton.Text = "Save"
saveUrlButton.TextColor3 = Color3.fromRGB(255, 255, 255)
saveUrlButton.TextSize = 13
saveUrlButton.Parent = urlRow
createCorner(saveUrlButton, 8)

local promptSection = createSection(root, "Agent")
createLabel(promptSection, "PromptHint", "Describe the prop you want. The backend will create a job and stream progress into the chat feed below.", 12, Color3.fromRGB(176, 184, 201))

local promptBox = Instance.new("TextBox")
promptBox.Name = "PromptBox"
promptBox.BackgroundColor3 = Color3.fromRGB(24, 27, 34)
promptBox.BorderSizePixel = 0
promptBox.ClearTextOnFocus = false
promptBox.Font = Enum.Font.Gotham
promptBox.MultiLine = true
promptBox.PlaceholderText = "create an Nvidia-themed event prop for Roblox"
promptBox.Size = UDim2.new(1, 0, 0, 96)
promptBox.Text = getSetting(SETTINGS.LAST_PROMPT, "")
promptBox.TextColor3 = Color3.fromRGB(235, 238, 244)
promptBox.TextSize = 13
promptBox.TextWrapped = true
promptBox.TextXAlignment = Enum.TextXAlignment.Left
promptBox.TextYAlignment = Enum.TextYAlignment.Top
promptBox.Parent = promptSection
createCorner(promptBox, 8)
createPadding(promptBox, 10, 10, 10, 10)

local actionRow = Instance.new("Frame")
actionRow.Name = "ActionRow"
actionRow.BackgroundTransparency = 1
actionRow.Size = UDim2.new(1, 0, 0, 32)
actionRow.Parent = promptSection

local actionLayout = Instance.new("UIListLayout")
actionLayout.FillDirection = Enum.FillDirection.Horizontal
actionLayout.Padding = UDim.new(0, 8)
actionLayout.Parent = actionRow

local generateButton = createButton(actionRow, "GenerateButton", "Generate Asset", Color3.fromRGB(35, 166, 125))
local refreshButton = createButton(actionRow, "RefreshButton", "Refresh", Color3.fromRGB(76, 110, 245))
local placeButton = createButton(actionRow, "PlaceButton", "Place In Studio", Color3.fromRGB(214, 137, 43))

local statusSection = createSection(root, "Job State")
local statusValue = createInfoLine(statusSection, "Status")
local jobIdValue = createInfoLine(statusSection, "Job ID")
local assetIdValue = createInfoLine(statusSection, "Asset ID")
local tagsValue = createInfoLine(statusSection, "Tags")
local exportPathValue = createInfoLine(statusSection, "Export Path")
local messageValue = createLabel(statusSection, "Message", "No job selected.", 12, Color3.fromRGB(176, 184, 201))

local feedSection = createSection(root, "Chat Feed")
createLabel(feedSection, "FeedHint", "User prompts, assistant replies, and pipeline events are merged here from `/chat` and `/status`.", 12, Color3.fromRGB(176, 184, 201))

local feedFrame = Instance.new("ScrollingFrame")
feedFrame.Name = "Feed"
feedFrame.Active = true
feedFrame.AutomaticCanvasSize = Enum.AutomaticSize.None
feedFrame.BackgroundColor3 = Color3.fromRGB(24, 27, 34)
feedFrame.BorderSizePixel = 0
feedFrame.CanvasSize = UDim2.new(0, 0, 0, 0)
feedFrame.ScrollBarImageColor3 = Color3.fromRGB(82, 91, 111)
feedFrame.ScrollBarThickness = 6
feedFrame.ScrollingDirection = Enum.ScrollingDirection.Y
feedFrame.ScrollingEnabled = true
feedFrame.Size = UDim2.new(1, 0, 0, 240)
feedFrame.Parent = feedSection
createCorner(feedFrame, 10)
createPadding(feedFrame, 6, 6, 6, 6)

local feedLayout = Instance.new("UIListLayout")
feedLayout.Padding = UDim.new(0, 8)
feedLayout.SortOrder = Enum.SortOrder.LayoutOrder
feedLayout.Parent = feedFrame

local currentBaseUrl = normalizeBaseUrl(urlBox.Text)
local currentJobId = getSetting(SETTINGS.LAST_JOB_ID, nil)
local currentStatus = nil
local currentAsset = nil
local currentPrompt = getSetting(SETTINGS.LAST_PROMPT, "")
local busy = false
local pollToken = 0

local function setStatusMessage(text, color)
	messageValue.Text = text
	messageValue.TextColor3 = color or Color3.fromRGB(176, 184, 201)
end

local function updateButtons()
	setButtonEnabled(generateButton, not busy, Color3.fromRGB(35, 166, 125))
	setButtonEnabled(refreshButton, (not busy) and currentJobId ~= nil, Color3.fromRGB(76, 110, 245))
	setButtonEnabled(placeButton, (not busy) and currentStatus == "exported" and currentAsset ~= nil, Color3.fromRGB(214, 137, 43))
end

local function updateStatePanel(assetPayload)
	statusValue.Text = currentStatus or "-"
	jobIdValue.Text = currentJobId or "-"

	if type(assetPayload) == "table" and type(assetPayload.asset) == "table" then
		local asset = assetPayload.asset
		currentAsset = assetPayload
		assetIdValue.Text = asset.asset_id or "-"
		tagsValue.Text = table.concat(asset.tags or {}, ", ")
		if tagsValue.Text == "" then
			tagsValue.Text = "-"
		end
		exportPathValue.Text = (assetPayload.paths and assetPayload.paths.export_path) or asset.export_path or "-"
	else
		currentAsset = nil
		assetIdValue.Text = "-"
		tagsValue.Text = "-"
		exportPathValue.Text = "-"
	end
end

local function clearFeed()
	for _, child in ipairs(feedFrame:GetChildren()) do
		if not child:IsA("UIListLayout") and not child:IsA("UICorner") and not child:IsA("UIPadding") then
			child:Destroy()
		end
	end
end

local function createFeedItem(item)
	local frame = Instance.new("Frame")
	frame.Name = "FeedItem"
	frame.BackgroundColor3 = Color3.fromRGB(32, 36, 46)
	frame.BorderSizePixel = 0
	frame.AutomaticSize = Enum.AutomaticSize.Y
	frame.Size = UDim2.new(1, 0, 0, 0)
	frame.Parent = feedFrame
	createCorner(frame, 8)
	createPadding(frame, 10, 10, 8, 8)

	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, 4)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = frame

	local title = Instance.new("TextLabel")
	title.BackgroundTransparency = 1
	title.Size = UDim2.new(1, 0, 0, 16)
	title.Font = Enum.Font.GothamSemibold
	title.Text = item.title
	title.TextColor3 = item.titleColor
	title.TextSize = 12
	title.TextXAlignment = Enum.TextXAlignment.Left
	title.Parent = frame

	local body = Instance.new("TextLabel")
	body.BackgroundTransparency = 1
	body.AutomaticSize = Enum.AutomaticSize.Y
	body.Size = UDim2.new(1, 0, 0, 0)
	body.Font = Enum.Font.Gotham
	body.Text = item.body
	body.TextColor3 = Color3.fromRGB(235, 238, 244)
	body.TextSize = 12
	body.TextWrapped = true
	body.TextXAlignment = Enum.TextXAlignment.Left
	body.TextYAlignment = Enum.TextYAlignment.Top
	body.Parent = frame

	if item.timestamp then
		local timestamp = Instance.new("TextLabel")
		timestamp.BackgroundTransparency = 1
		timestamp.Size = UDim2.new(1, 0, 0, 14)
		timestamp.Font = Enum.Font.Code
		timestamp.Text = item.timestamp
		timestamp.TextColor3 = Color3.fromRGB(138, 146, 163)
		timestamp.TextSize = 11
		timestamp.TextXAlignment = Enum.TextXAlignment.Left
		timestamp.Parent = frame
	end
end

local function renderFeed(chatPayload, statusPayload)
	clearFeed()

	local items = {}
	if type(chatPayload) == "table" and type(chatPayload.messages) == "table" then
		for _, message in ipairs(chatPayload.messages) do
			local role = message.role or "assistant"
			local title
			local titleColor
			if role == "user" then
				title = "You"
				titleColor = Color3.fromRGB(111, 186, 255)
			else
				title = "Agent"
				titleColor = Color3.fromRGB(124, 222, 173)
			end
			table.insert(items, {
				timestamp = message.timestamp,
				title = title,
				titleColor = titleColor,
				body = message.content or "",
			})
		end
	end

	if type(statusPayload) == "table" and type(statusPayload.events) == "table" then
		for _, event in ipairs(statusPayload.events) do
			table.insert(items, {
				timestamp = event.timestamp,
				title = "Pipeline · " .. tostring(event.status or "unknown"),
				titleColor = Color3.fromRGB(255, 196, 113),
				body = event.message or "",
			})
		end
	end

	table.sort(items, function(a, b)
		local left = a.timestamp or ""
		local right = b.timestamp or ""
		if left == right then
			return a.title < b.title
		end
		return left < right
	end)

	if #items == 0 then
		createFeedItem({
			title = "No messages yet",
			titleColor = Color3.fromRGB(176, 184, 201),
			body = "Submit a prompt or refresh an existing job to populate the feed.",
		})
	else
		for _, item in ipairs(items) do
			createFeedItem(item)
		end
	end

	task.defer(function()
		local contentHeight = feedLayout.AbsoluteContentSize.Y + 12
		local maxOffset = math.max(0, contentHeight - feedFrame.AbsoluteSize.Y)
		feedFrame.CanvasPosition = Vector2.new(0, maxOffset)
	end)
end

rootLayout:GetPropertyChangedSignal("AbsoluteContentSize"):Connect(function()
	root.CanvasSize = UDim2.new(0, 0, 0, rootLayout.AbsoluteContentSize.Y + 24)
end)

feedLayout:GetPropertyChangedSignal("AbsoluteContentSize"):Connect(function()
	feedFrame.CanvasSize = UDim2.new(0, 0, 0, feedLayout.AbsoluteContentSize.Y + 12)
end)

local function saveBaseUrl()
	currentBaseUrl = normalizeBaseUrl(urlBox.Text)
	urlBox.Text = currentBaseUrl
	setSetting(SETTINGS.BASE_URL, currentBaseUrl)
	setStatusMessage("Saved backend URL: " .. currentBaseUrl, Color3.fromRGB(124, 222, 173))
end

local function refreshJob(jobId)
	local statusPayload = requestJson("GET", currentBaseUrl, "/api/jobs/" .. jobId .. "/status")
	local chatPayload = requestJson("GET", currentBaseUrl, "/api/jobs/" .. jobId .. "/chat")
	local assetPayload = requestJson("GET", currentBaseUrl, "/api/jobs/" .. jobId .. "/asset")

	currentJobId = jobId
	currentStatus = statusPayload.status
	if type(chatPayload) == "table" and type(chatPayload.messages) == "table" then
		for _, message in ipairs(chatPayload.messages) do
			if message.role == "user" and type(message.content) == "string" then
				currentPrompt = message.content
			end
		end
	end
	setSetting(SETTINGS.LAST_JOB_ID, currentJobId)
	updateStatePanel(assetPayload)
	renderFeed(chatPayload, statusPayload)

	if currentStatus == "failed" then
		setStatusMessage(statusPayload.error or "The pipeline failed.", Color3.fromRGB(255, 132, 132))
	elseif currentStatus == "placed" then
		setStatusMessage("Asset has already been placed into Studio.", Color3.fromRGB(124, 222, 173))
	elseif currentStatus == "exported" then
		setStatusMessage("Asset exported. Use Place In Studio to drop a proxy model into Workspace.", Color3.fromRGB(255, 211, 124))
	else
		setStatusMessage("Job is " .. tostring(currentStatus) .. ".", Color3.fromRGB(176, 184, 201))
	end

	updateButtons()
	return statusPayload
end

local function setBusy(nextBusy)
	busy = nextBusy
	updateButtons()
end

local function stopPolling()
	pollToken = pollToken + 1
end

local function startPolling(jobId)
	stopPolling()
	local token = pollToken
	task.spawn(function()
		while token == pollToken and currentJobId == jobId do
			local ok, statusPayload = pcall(function()
				return refreshJob(jobId)
			end)
			if not ok then
				setStatusMessage("Polling failed: " .. tostring(statusPayload), Color3.fromRGB(255, 132, 132))
				break
			end
			if TERMINAL_STATES[statusPayload.status] then
				break
			end
			task.wait(POLL_INTERVAL_SECONDS)
		end
	end)
end

local function hashPromptToColor(prompt)
	local total = 0
	for i = 1, #prompt do
		total = (total + string.byte(prompt, i) * i) % 255
	end
	return Color3.fromHSV((total % 255) / 255, 0.55, 0.95)
end

local function createMetadataValue(parent, className, name, value)
	local instance = Instance.new(className)
	instance.Name = name
	instance.Value = value
	instance.Parent = parent
	return instance
end

local function placeProxyAsset(assetPayload)
	local asset = assetPayload.asset or {}
	local paths = assetPayload.paths or {}
	local prompt = asset.prompt or currentPrompt or ""
	local model = Instance.new("Model")
	model.Name = asset.asset_id or ("VibeVerse_" .. (assetPayload.job_id or "Asset"))
	model:SetAttribute("VibeVerseJobId", assetPayload.job_id or "")
	model:SetAttribute("VibeVerseAssetId", asset.asset_id or "")
	model:SetAttribute("VibeVersePrompt", prompt)
	model:SetAttribute("VibeVerseExportPath", paths.export_path or asset.export_path or "")
	model:SetAttribute("VibeVerseMetadataPath", paths.metadata_path or asset.metadata_path or "")
	model:SetAttribute("VibeVerseStatus", assetPayload.status or "")

	local part = Instance.new("Part")
	part.Name = "GeneratedAssetProxy"
	part.Size = Vector3.new(6, 6, 6)
	part.Anchored = true
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.Color = hashPromptToColor(prompt)
	part.Material = Enum.Material.SmoothPlastic
	part.Parent = model

	local decal = Instance.new("Decal")
	decal.Face = Enum.NormalId.Front
	decal.Texture = "rbxassetid://7108510958"
	decal.Transparency = 0.25
	decal.Parent = part

	local billboard = Instance.new("BillboardGui")
	billboard.Name = "Info"
	billboard.AlwaysOnTop = true
	billboard.Size = UDim2.new(0, 220, 0, 64)
	billboard.StudsOffset = Vector3.new(0, 4.5, 0)
	billboard.Parent = part

	local label = Instance.new("TextLabel")
	label.BackgroundColor3 = Color3.fromRGB(20, 22, 28)
	label.BackgroundTransparency = 0.15
	label.BorderSizePixel = 0
	label.Size = UDim2.new(1, 0, 1, 0)
	label.Font = Enum.Font.GothamSemibold
	label.Text = string.format("VibeVerse\n%s", asset.asset_id or assetPayload.job_id or "asset")
	label.TextColor3 = Color3.fromRGB(245, 247, 252)
	label.TextScaled = true
	label.Parent = billboard
	createCorner(label, 8)

	local metadata = Instance.new("Configuration")
	metadata.Name = "Metadata"
	metadata.Parent = model

	createMetadataValue(metadata, "StringValue", "Prompt", prompt)
	createMetadataValue(metadata, "StringValue", "JobId", assetPayload.job_id or "")
	createMetadataValue(metadata, "StringValue", "AssetId", asset.asset_id or "")
	createMetadataValue(metadata, "StringValue", "ExportPath", paths.export_path or asset.export_path or "")
	createMetadataValue(metadata, "StringValue", "MetadataPath", paths.metadata_path or asset.metadata_path or "")
	createMetadataValue(metadata, "StringValue", "Tags", table.concat(asset.tags or {}, ","))

	local camera = workspace.CurrentCamera
	local targetPosition
	if camera then
		targetPosition = camera.CFrame.Position + camera.CFrame.LookVector * 18
	else
		targetPosition = Vector3.new(0, 5, 0)
	end
	part.CFrame = CFrame.new(targetPosition)

	model.Parent = workspace
	model.PrimaryPart = part
	Selection:Set({model})
	ChangeHistoryService:SetWaypoint("VibeVerse Place Proxy Asset")
	return model
end

local function submitPrompt()
	local prompt = trim(promptBox.Text)
	if prompt == "" then
		setStatusMessage("Prompt is required.", Color3.fromRGB(255, 132, 132))
		return
	end

	saveBaseUrl()
	currentPrompt = prompt
	setSetting(SETTINGS.LAST_PROMPT, prompt)
	setBusy(true)

	local ok, result = pcall(function()
		return requestJson("POST", currentBaseUrl, "/api/jobs", {
			prompt = prompt,
		})
	end)

	setBusy(false)
	if not ok then
		setStatusMessage("Failed to create job: " .. tostring(result), Color3.fromRGB(255, 132, 132))
		return
	end

	local job = result.job or {}
	currentJobId = job.job_id
	currentStatus = job.status or "queued"
	updateStatePanel(nil)
	renderFeed({ messages = job.messages or {} }, { events = job.events or {}, status = currentStatus })
	setStatusMessage("Job created. Polling backend for updates...", Color3.fromRGB(124, 222, 173))
	updateButtons()
	startPolling(currentJobId)
end

local function refreshCurrentJob()
	if not currentJobId then
		setStatusMessage("No job selected yet.", Color3.fromRGB(255, 211, 124))
		return
	end

	saveBaseUrl()
	setBusy(true)
	local ok, err = pcall(function()
		refreshJob(currentJobId)
	end)
	setBusy(false)

	if not ok then
		setStatusMessage("Refresh failed: " .. tostring(err), Color3.fromRGB(255, 132, 132))
		return
	end

	if not TERMINAL_STATES[currentStatus] then
		startPolling(currentJobId)
	end
end

local function placeCurrentJob()
	if currentStatus ~= "exported" or currentAsset == nil then
		setStatusMessage("Wait until the job reaches exported before placing it.", Color3.fromRGB(255, 211, 124))
		return
	end

	setBusy(true)
	local ok, placedModel = pcall(function()
		return placeProxyAsset(currentAsset)
	end)

	if not ok then
		setBusy(false)
		setStatusMessage("Failed to place proxy asset: " .. tostring(placedModel), Color3.fromRGB(255, 132, 132))
		return
	end

	local markedPlaced, result = pcall(function()
		return requestJson("POST", currentBaseUrl, "/api/jobs/" .. currentJobId .. "/placed", {})
	end)
	setBusy(false)

	if not markedPlaced then
		setStatusMessage(
			"Proxy placed in Studio, but backend update failed: " .. tostring(result),
			Color3.fromRGB(255, 211, 124)
		)
		return
	end

	currentStatus = result.job and result.job.status or "placed"
	updateButtons()
	setStatusMessage("Placed proxy asset into Workspace and marked the job as placed.", Color3.fromRGB(124, 222, 173))
	refreshCurrentJob()
	Selection:Set({placedModel})
end

toggleButton.Click:Connect(function()
	widget.Enabled = not widget.Enabled
	if widget.Enabled and currentJobId and currentStatus ~= "placed" then
		refreshCurrentJob()
	end
end)

widget:GetPropertyChangedSignal("Enabled"):Connect(function()
	toggleButton:SetActive(widget.Enabled)
end)

saveUrlButton.MouseButton1Click:Connect(saveBaseUrl)

urlBox.FocusLost:Connect(function(enterPressed)
	if enterPressed then
		saveBaseUrl()
	end
end)

generateButton.MouseButton1Click:Connect(submitPrompt)
refreshButton.MouseButton1Click:Connect(refreshCurrentJob)
placeButton.MouseButton1Click:Connect(placeCurrentJob)

plugin.Unloading:Connect(stopPolling)
toggleButton:SetActive(widget.Enabled)

if currentJobId then
	local ok, err = pcall(function()
		refreshJob(currentJobId)
	end)
	if not ok then
		setStatusMessage("Saved job could not be refreshed: " .. tostring(err), Color3.fromRGB(255, 132, 132))
	end
else
	updateStatePanel(nil)
	renderFeed(nil, nil)
	updateButtons()
end
