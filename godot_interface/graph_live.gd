extends Node2D
"""
Visualisation du dernier step_*.json en temps réel,
en ouvrant un dossier Windows absolu.
"""

@export var folder_path : String = "C:/Users/maxim/Wb_theorie/rp2_wb_model/outputs/snapshots"
@export var refresh_ms  : int    = 200

const SCALE    : float = 6.0
const TS_COL   : Color = Color.RED
const EDGE_COL : Color = Color(0.7,0.7,0.7,0.3)
const P_COL    : Color = Color(0.3,0.3,0.3)
const A_COL    : Color = Color(0.2,0.8,0.2)

var nodes : Dictionary = {}  # id -> node data
var edges : Array      = []

var timer : Timer

# Toggles
var show_normal_edges : bool = true
var show_inactive_nodes : bool = true

func _ready() -> void:
	# Installe le timer pour relire le dossier
	timer = Timer.new()
	timer.wait_time = float(refresh_ms) / 1000.0
	timer.one_shot = false
	timer.connect("timeout", Callable(self, "_on_timer"))
	add_child(timer)
	timer.start()
	# Premier chargement
	_on_timer()

func _on_timer() -> void:
	# Ouvre le dossier absolu Windows
	var dir = DirAccess.open(folder_path)
	if dir == null:
		push_error("Impossible d’ouvrir le dossier : %s" % folder_path)
		return

	# Liste les fichiers JSON step_*.json
	var files := []
	dir.list_dir_begin()
	var f := dir.get_next()
	while f != "":
		if not dir.current_is_dir() and f.begins_with("step_") and f.ends_with(".json"):
			files.append(f)
		f = dir.get_next()
	dir.list_dir_end()
	files.sort()

	# Charge le plus récent
	if files.size() > 0:
		var last = files[files.size() - 1]
		_load_state(folder_path + "/" + last)


func _load_state(path : String) -> void:
	var txt = FileAccess.get_file_as_string(path)
	var json = JSON.new()
	var error = json.parse(txt)
	if error != OK:
		push_error("JSON parse error: %s" % json.get_error_message())
		return
	var data = json.get_data()

	# Reconstruire nodes et edges
	nodes.clear()
	for n in data["nodes"]:
		nodes[int(n["id"])] = n

	edges.clear()
	for e in data["edges"]:
		var u = int(e["u"])
		var v = int(e["v"])
		if nodes.has(u) and nodes.has(v):
			edges.append(e)

	queue_redraw()  # déclenche _draw()

func _draw() -> void:
	# Dessine tous les liens
	for e in edges:
		var a = _coord(int(e["u"]))
		var b = _coord(int(e["v"]))
		var col = TS_COL if bool(e.get("is_ts", false)) else EDGE_COL
		if e.get("is_ts", false):
			draw_line(a, b, col, 1.0)
		elif show_normal_edges:
			# Ne dessiner les arêtes normales que si les deux ρ > 0.4
			var rho_u = float(nodes[int(e["u"])].get("rho", 0.0))
			var rho_v = float(nodes[int(e["v"])].get("rho", 0.0))
			if rho_u > 0.4 and rho_v > 0.4:
				draw_line(a, b, EDGE_COL, 0.3)
	# Dessine tous les nœuds
	for id in nodes.keys():
		var n = nodes[id]
		if not show_inactive_nodes and n["sigma"] != 1:
			continue
		var pos = _coord(id)
		var base = A_COL if n["sigma"] == 1  else P_COL
		var rho = clampf(float(n.get("rho", 0.0)), 0.0, 1.0)
		var col = base.lerp(Color(1,1,1), rho)
		var r = 2.0 + 6.0 * clampf(float(n["rho"]), 0.0, 1.0)
		draw_circle(pos, r, col)

func _coord(id : int) -> Vector2:
	var n = nodes[id]

	# Vérifier si les coordonnées existent
	if n.has("x") and n.has("y"):
		return Vector2(n["x"], n["y"]) * SCALE
	else:
		# Utiliser une disposition plus naturelle
		# Basée sur un algorithme de "sunflower" pour une distribution plus uniforme
		var node_count = nodes.size()
		var golden_ratio = 1.618033988749895
		var i = float(id)

		# Utiliser le ratio d'or pour une distribution plus naturelle
		var r = sqrt(i / node_count) * sqrt(node_count) * 2
		var theta = i * 2 * PI / golden_ratio

		# Ajouter un peu de bruit pour éviter l'alignement parfait
		var noise_factor = 0.2
		r += randf_range(-noise_factor, noise_factor) * r
		theta += randf_range(-noise_factor, noise_factor) * 0.1

		return Vector2(cos(theta) * r, sin(theta) * r) * SCALE

func _unhandled_input(event : InputEvent) -> void:
	if event is InputEventKey and event.pressed:
		match event.keycode:
			KEY_E:
				show_normal_edges = !show_normal_edges
				queue_redraw()
			KEY_N:
				show_inactive_nodes = !show_inactive_nodes
				queue_redraw()
	elif event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			$Camera2D.zoom *= Vector2(1.1,1.1)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			$Camera2D.zoom *= Vector2(0.9,0.9)
