extends Node2D
"""
Visualisation temps-réel du dernier step_*.json
• Arêtes TS (rouge)
• Arêtes normales (gris) filtrées
• Nœuds coloriés selon φ (HSV) et dimensionnés selon ρ
• E = toggle arêtes normales, N = toggle nœuds inactifs
• Molette pour zoom
"""

@export var folder_path : String = "C:/Users/maxim/Wb_theorie/rp2_wb_model/outputs/snapshots"
@export var refresh_ms  : int    = 200

const SCALE    : float = 6.0
const TS_COL   : Color = Color(1.0,0.0,0.0,0.2)
const EDGE_COL : Color = Color(0.7,0.7,0.7,0.2)
const P_COL    : Color = Color(0.3,0.3,0.3)   # inactive
const A_COL    : Color = Color(0.2,0.8,0.2)   # active

var nodes : Dictionary = {}   # id -> node data
var edges : Array      = []   # liste des arêtes

var timer : Timer

# Toggles
var show_normal_edges   : bool = true
var show_inactive_nodes : bool = true

func _ready() -> void:
	# Timer de rafraîchissement
	timer = Timer.new()
	timer.wait_time = float(refresh_ms) / 1000.0
	timer.one_shot = false
	timer.timeout.connect(Callable(self, "_on_timer"))
	add_child(timer)
	timer.start()
	# Premier chargement
	_on_timer()

func _on_timer() -> void:
	var dir = DirAccess.open(folder_path)
	if dir == null:
		push_error("Impossible d’ouvrir le dossier : %s" % folder_path)
		return

	# Recherche des fichiers step_*.json
	var files = []
	dir.list_dir_begin()
	var f = dir.get_next()
	while f != "":
		if dir.current_is_dir() == false and f.begins_with("step_") and f.ends_with(".json"):
			files.append(f)
		f = dir.get_next()
	dir.list_dir_end()
	files.sort()

	if files.size() == 0:
		return

	# Charger le plus récent
	var last = files[files.size() - 1]
	_load_state(folder_path + "/" + last)

func _load_state(path : String) -> void:
	var txt = FileAccess.get_file_as_string(path)
	var j = JSON.new()
	var err = j.parse(txt)
	if err != OK:
		push_error("JSON parse error: %s" % j.get_error_message())
		return
	var data = j.get_data()

	# Reconstruire nodes
	nodes.clear()
	for entry in data["nodes"]:
		var nid = int(entry["id"])
		nodes[nid] = entry

	# Reconstruire et filtrer edges
	edges.clear()
	for entry in data["edges"]:
		var u = int(entry["u"])
		var v = int(entry["v"])
		if nodes.has(u) and nodes.has(v):
			edges.append(entry)

	queue_redraw()

func _draw() -> void:
	# 1) Arêtes
	for entry in edges:
		var u = int(entry["u"])
		var v = int(entry["v"])
		var a = _coord(u)
		var b = _coord(v)
		var is_ts = false
		if entry.has("is_ts") and bool(entry["is_ts"]) == true:
			is_ts = true

		if is_ts:
			draw_line(a, b, TS_COL, 0.7)
		else:
			if show_normal_edges:
				var rho_u = 0.0
				var rho_v = 0.0
				if nodes[u].has("rho"):
					rho_u = float(nodes[u]["rho"])
				if nodes[v].has("rho"):
					rho_v = float(nodes[v]["rho"])
				if rho_u > 0.4 and rho_v > 0.4:
					draw_line(a, b, EDGE_COL, 0.3)

	# 2) Nœuds
	for id in nodes.keys():
		var n = nodes[id]
		# Filtre inactifs
		if show_inactive_nodes == false and n.has("sigma") and int(n["sigma"]) != 1:
			continue

		var pos = _coord(id)

		# Récupération de rho
		var rho = 0.0
		if n.has("rho"):
			rho = clampf(float(n["rho"]), 0.0, 1.0)

		# Récupération de phi
		var phi = 0.0
		if n.has("phi"):
			phi = float(n["phi"])

		# Calcul de la teinte HSV
		var hue = clampf(float(n.get("phi",0.0)), 0.0, 1.0)
		var sat = 1.0
		var val = rho
		if val < 0.2:
			val = 0.2  # pour rendre visible même rho=0
		var col = Color.from_hsv(hue, sat, val)

		# Taille selon rho
		var radius = 2.0 + 5.0 * rho

		draw_circle(pos, radius, col)

func _coord(id : int) -> Vector2:
	var n = nodes[id]
	if n.has("x") and n.has("y"):
		return Vector2(float(n["x"]), float(n["y"])) * SCALE
	# fallback sunflower
	var count = nodes.size()
	var i = float(id)
	var r = sqrt(i / count) * sqrt(count) * 2.0
	var theta = i * 2.0 * PI / 1.618033988749895
	r += randf_range(-0.2, 0.2) * r
	theta += randf_range(-0.2, 0.2)
	return Vector2(cos(theta) * r, sin(theta) * r) * SCALE

func _unhandled_input(event : InputEvent) -> void:
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_E:
			show_normal_edges = not show_normal_edges
			queue_redraw()
		elif event.keycode == KEY_N:
			show_inactive_nodes = not show_inactive_nodes
			queue_redraw()
	elif event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			$Camera2D.zoom *= Vector2(1.1, 1.1)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			$Camera2D.zoom *= Vector2(0.9, 0.9)
