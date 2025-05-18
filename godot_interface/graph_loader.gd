extends Node2D

# Chargeur de graphe RP2 pour Godot
# Ce script charge les fichiers JSON exportés par le modèle Python
# et les affiche dans l'environnement Godot

# Paramètres configurables
@export var json_file_path: String = "res://outputs/model_state.json"
@export var node_scene: PackedScene  # Scène pour les nœuds du graphe
@export var edge_scene: PackedScene  # Scène pour les liens du graphe
@export var scale_factor: float = 100.0  # Facteur d'échelle pour la visualisation

# Dictionnaires pour stocker les nœuds et liens
var nodes = {}
var edges = []
var graph_data = null

func _ready():
	# Charger le graphe au démarrage
	load_graph()

# Charge le graphe depuis un fichier JSON
func load_graph(file_path = null):
	if file_path:
		json_file_path = file_path
	
	# Nettoyer les nœuds et liens existants
	clear_graph()
	
	# Charger le fichier JSON
	var file = FileAccess.open(json_file_path, FileAccess.READ)
	if not file:
		print("Erreur: Impossible d'ouvrir le fichier ", json_file_path)
		return false
	
	var json_text = file.get_as_text()
	file.close()
	
	# Parser le JSON
	var json = JSON.new()
	var error = json.parse(json_text)
	if error != OK:
		print("Erreur JSON: ", json.get_error_message(), " à la ligne ", json.get_error_line())
		return false
	
	graph_data = json.get_data()
	
	# Créer les nœuds
	create_nodes()
	
	# Créer les liens
	create_edges()
	
	print("Graphe chargé: ", len(nodes), " nœuds, ", len(edges), " liens")
	return true

# Crée les nœuds du graphe
func create_nodes():
	if not graph_data or not graph_data.has("nodes"):
		return
	
	for node_id in graph_data.nodes:
		var node_data = graph_data.nodes[node_id]
		
		# Instancier la scène du nœud
		var node_instance = node_scene.instantiate()
		add_child(node_instance)
		
		# Positionner le nœud
		var pos = node_data.position
		node_instance.position = Vector2(pos.x * scale_factor, pos.y * scale_factor)
		
		# Configurer l'apparence du nœud selon les champs
		if node_instance.has_method("set_fields"):
			node_instance.set_fields(
				node_data.rho,  # Densité
				node_data.phi,  # Phase
				node_data.sigma  # Spin
			)
		
		# Stocker le nœud
		nodes[node_id] = node_instance

# Crée les liens du graphe
func create_edges():
	if not graph_data or not graph_data.has("edges"):
		return
	
	for edge_data in graph_data.edges:
		var source_id = edge_data.source
		var target_id = edge_data.target
		
		# Vérifier que les nœuds existent
		if not nodes.has(source_id) or not nodes.has(target_id):
			continue
		
		# Instancier la scène du lien
		var edge_instance = edge_scene.instantiate()
		add_child(edge_instance)
		
		# Configurer le lien
		if edge_instance.has_method("set_nodes"):
			edge_instance.set_nodes(nodes[source_id], nodes[target_id])
		
		# Stocker le lien
		edges.append(edge_instance)

# Nettoie le graphe en supprimant tous les nœuds et liens
func clear_graph():
	# Supprimer les liens
	for edge in edges:
		if is_instance_valid(edge):
			edge.queue_free()
	edges.clear()
	
	# Supprimer les nœuds
	for node_id in nodes:
		if is_instance_valid(nodes[node_id]):
			nodes[node_id].queue_free()
	nodes.clear()

# Met à jour le graphe avec un nouveau fichier
func update_graph(file_path):
	return load_graph(file_path)

# Anime la transition entre deux états du graphe
func animate_transition(start_file, end_file, duration = 1.0):
	# Charger l'état initial
	if not load_graph(start_file):
		return false
	
	# Charger l'état final dans une structure temporaire
	var file = FileAccess.open(end_file, FileAccess.READ)
	if not file:
		return false
	
	var json_text = file.get_as_text()
	file.close()
	
	var json = JSON.new()
	var error = json.parse(json_text)
	if error != OK:
		return false
	
	var end_data = json.get_data()
	
	# Créer une animation pour chaque nœud
	for node_id in nodes:
		if end_data.nodes.has(node_id):
			var start_pos = nodes[node_id].position
			var end_pos = Vector2(
				end_data.nodes[node_id].position.x * scale_factor,
				end_data.nodes[node_id].position.y * scale_factor
			)
			
			# Créer un Tween pour animer la position
			var tween = create_tween()
			tween.tween_property(nodes[node_id], "position", end_pos, duration)
			
			# Animer les champs si la méthode existe
			if nodes[node_id].has_method("animate_fields"):
				nodes[node_id].animate_fields(
					end_data.nodes[node_id].rho,
					end_data.nodes[node_id].phi,
					end_data.nodes[node_id].sigma,
					duration
				)
	
	# Attendre la fin de l'animation puis charger l'état final
	await get_tree().create_timer(duration).timeout
	load_graph(end_file)
	
	return true
