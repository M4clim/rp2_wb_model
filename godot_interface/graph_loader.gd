"""
Chargement et visualisation d'un fichier JSON exporté par exporter.py.
• Affiche les nœuds (couleur en fonction de σ / ρ)
• Colore les liens TS en rouge.
A coller dans un Node2D (root) d'une scène Godot 4.
"""

extends Node2D

@export var json_path: String = "res://outputs/step_0.json"
@onready var camera := $Camera2D

const NODE_SIZE := 8.0
const TS_COLOR := Color.RED
const NORMAL_COLOR := Color.WHITE
const P_COLOR := Color("2b2d42")
const A_COLOR := Color("ef233c")

func _ready():
    load_graph(json_path)

func load_graph(path: String):
    var file := FileAccess.open(path, FileAccess.READ)
    if not file:
        push_error("Cannot open %s" % path)
        return
    var data := JSON.parse_string(file.get_as_text())
    var nodes := data["nodes"]
    var edges := data["edges"]
    # Draw edges first
    for e in edges:
        var u = nodes[e["u"]]
        var v = nodes[e["v"]]
        var color = TS_COLOR if e["is_ts"] else NORMAL_COLOR
        draw_line(Vector2(u["x"], u["y"]) * NODE_SIZE, Vector2(v["x"], v["y"]) * NODE_SIZE, color, 2.0)
    # Draw nodes
    for n in nodes:
        var pos = Vector2(n["x"], n["y"]) * NODE_SIZE
        var col = A_COLOR if n["sigma"] == 1 else P_COLOR
        draw_circle(pos, 3.0, col)

func _input(event):
    # zoom with mouse wheel
    if event is InputEventMouseButton and event.pressed:
        var factor := 1.1 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 0.9
        camera.zoom *= Vector2(factor, factor)
