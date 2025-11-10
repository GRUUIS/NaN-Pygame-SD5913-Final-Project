"""Simple door routing table stub.
Return a mapping that other code can import. This is intentionally tiny; you
can expand it later to point door names to target map names.
"""

DOOR_ROUTES = {
	# example: 'map01:left_door': 'map02:right_door'
}


def get_route(door_id):
	"""Return target route for a door id or None if unknown."""
	return DOOR_ROUTES.get(door_id)
