'''
Socket utility for MorgHTTPClient plugin.
'''

from requests.exceptions import ConnectionError
from typing import List, Union, Tuple
import requests
import time


class SocketError(Exception):
	def __init__(self, error_message: str, endpoint: str):
		self.__error_message = error_message
		self.__endpoint = endpoint
		super().__init__(self.get_error())

	def get_error(self):
		return f"{self.__error_message} endpoint: '{self.__endpoint}'"


class Socket:

	# TODO: ID/NPC ID/Object ID conversion function/dict to get the readable name of an object

	def __init__(self):
		self.base_endpoint = "http://localhost:8081/"

		self.inv_endpoint = "inv"
		self.stats_endpoint = "stats"
		self.equip_endpoint = "equip"
		self.events_endpoint = "events"

		self.timeout = 1

	def __do_get(self, endpoint: str) -> dict:
		'''
		Args:
			endpoint: One of either "inv", "stats", "equip", "events"
		Returns:
			All JSON data from the endpoint as a dict.
		Raises:
			SocketError: If the endpoint is not valid or the server is not running.
		'''
		try:
			response = requests.get(f"{self.base_endpoint}{endpoint}", timeout=self.timeout)
		except ConnectionError as e:
			raise SocketError("Unable to reach socket", endpoint) from e

		if response.status_code != 200:
			if response.status_code == 204:
				raise SocketError(
					f"Endpoint not available, make sure you are fully logged in, status code: {response.status_code}",
					endpoint)
			else:
				raise SocketError(f"Unable to reach socket, status code: {response.status_code}", endpoint)

		return response.json()

	def __test_endpoints(self) -> bool:
		"""
		Ensures all endpoints are working correctly to avoid errors happening when any method is called

		Returns:
			True if successful False otherwise
		"""
		for i in list(self.__dict__.values())[1:-1]:  # Look away
			try:
				self.__do_get(endpoint=i)
			except SocketError as e:
				print(e)
				print(f"Endpoint '{i}' is not working.")
				return False
		return True

	def get_hitpoints(self) -> Union[Tuple[int, int], None]:
		'''
		Fetches the current and maximum hitpoints of the player.
		Returns:
			A Tuple(current_hitpoints, maximum_hitpoints), or None if an error occurred.
		'''
		try:
			data = self.__do_get(endpoint=self.events_endpoint)
		except SocketError as e:
			print(e)
			return None
		hitpoints_data = data['health']
		cur_hp, max_hp = hitpoints_data.split("/")  # hitpoints_data example = "21/21"
		return int(cur_hp), int(max_hp)

	def run_energy(self) -> Union[int, None]:
		'''
		Fetches the current run energy of the player.
		Returns:
			An int representing the current run energy, or None if an error occurred.
		'''
		try:
			data = self.__do_get(endpoint=self.events_endpoint)
		except SocketError as e:
			print(e)
			return None
		return int(data['run energy'])

	def get_animation(self) -> Union[int, None]:
		'''
		Fetches the current animation. (Unknown usage)
		Returns:
			An int representing the current animation, or None if an error occurred.
		'''
		try:
			data = self.__do_get(endpoint=self.events_endpoint)
		except SocketError as e:
			print(e)
			return None
		return int(data['animation'])

	def get_animation_id(self) -> Union[int, None]:
		'''
		Fetches the current animation ID of the player. Useful for checking if the player is doing
		a particular action.
		Returns:
			An int representing the current animation ID, or None if an error occurred.
		'''
		try:
			data = self.__do_get(endpoint=self.events_endpoint)
		except SocketError as e:
			print(e)
			return None
		return int(data['animation pose'])

	def get_is_player_idle(self) -> Union[bool, None]:
		'''
		Checks if the player is doing an idle animation.
		Returns:
			True if the player is idle, False otherwise, or None if an error occurred.
		'''
		try:
			data = self.__do_get(endpoint=self.events_endpoint)
		except SocketError as e:
			print(e)
			return None
		# TODO: These are idle animations but there may be more
		return data['animation pose'] in [808, 813]

	def get_stat_level(self, stat_name: str) -> Union[int, None]:
		'''
		Gets level of inputted stat
		Args:
			stat_name: the name of the stat (not case sensitive)
		Returns:
			The level of the stat as an int, or None if an error occurred.
		'''
		# TODO: Make class for stat_names to make invalid names impossible
		stat_name = stat_name.lower().capitalize()
		try:
			data = self.__do_get(endpoint=self.stats_endpoint)
		except SocketError as e:
			print(e)
			return None

		try:
			level = next(int(i['level']) for i in data[1:] if i['stat'] == stat_name)
		except StopIteration:
			print(f"Invalid stat name: {stat_name}")
			return None

		return level

	def get_stat_xp(self, stat_name: str) -> Union[int, None]:
		'''
		Gets the total xp of a stat.
		Args:
			stat_name: the name of the stat (not case sensitive)
		Returns:
			The total xp of the stat as an int, or None if an error occurred.
		'''
		stat_name = stat_name.lower().capitalize()
		try:
			data = self.__do_get(endpoint=self.stats_endpoint)
		except SocketError as e:
			print(e)
			return None

		try:
			total_xp = next(int(i['xp']) for i in data[1:] if i['stat'] == stat_name)
		except StopIteration:
			print(f"Invalid stat name: {stat_name}")
			return None

		return total_xp

	def get_stat_xp_gained(self, stat_name: str) -> Union[int, None]:
		'''
		Gets the xp gained of a stat. The tracker begins at 0 on client startup.
		Args:
			stat_name: the name of the stat (not case sensitive)
		Returns:
			The xp gained of the stat as an int, or None if an error occurred.
		'''
		stat_name = stat_name.lower().capitalize()  # Ensures str is formatted correctly for socket json key
		try:
			data = self.__do_get(endpoint=self.stats_endpoint)
		except SocketError as e:
			print(e)
			return None

		try:
			xp_gained = next(int(i['xp gained']) for i in data[1:] if i['stat'] == stat_name)
		except StopIteration:
			print(f"Invalid stat name: {stat_name}")
			return None

		return xp_gained

	def wait_til_gained_xp(
			self,
			stat_name: str,
			wait_time: int = 1
	) -> Union[int, None]:
		'''
		Waits until the player has gained xp in the inputted stat.
		Args:
			stat_name: the name of the stat (not case sensitive)
			wait_time: the time in seconds to wait
		Returns:
			The xp gained of the stat as an int, or None if an error occurred.
		'''
		stat_name = stat_name.lower().capitalize()  # Ensures str is formatted correctly for socket json key

		starting_xp = self.get_stat_xp(stat_name)
		if starting_xp is None:
			print("Failed to get starting xp.")
			return None
			
		stop_time = time.time() + wait_time
		while time.time() < stop_time:

			try:
				data = self.__do_get(endpoint=self.stats_endpoint)
			except SocketError as e:
				print(e)
				return None

			final_xp = next(int(i['xp']) for i in data[1:] if i['stat'] == stat_name)
			if final_xp > starting_xp:
				return final_xp

		return None

	def get_game_tick(self) -> Union[int, None]:
		'''
		Fetches game tick number.
		Returns:
			An int representing the current game tick, or None if an error occurred.
		'''
		try:
			data = self.__do_get(endpoint=self.events_endpoint)
		except SocketError as e:
			print(e)
			return None

		return int(data['game tick'])

	def get_player_position(self) -> Union[SocketError, Tuple[int, int, int]]:
		'''
		Fetches the world point of a player.
		Returns:
			A tuple of ints representing the player's world point (x, y, z),
			or None if an error occurred.
		'''
		try:
			data = self.__do_get(endpoint=self.events_endpoint)
		except SocketError as e:
			print(e)
			return None

		return int(data['worldPoint']['x']), int(data['worldPoint']['y']), int(data['worldPoint']['plane'])

	def get_player_region_data(self) -> Union[Tuple[int, int, int], None]:
		'''
		Fetches region data of a player's position.
		Returns:
			A tuple of ints representing the player's region data (region_x, region_y, region_ID),
			or None if an error occurred.
		'''
		try:
			data = self.__do_get(endpoint=self.events_endpoint)
		except SocketError as e:
			print(e)
			return None

		return int(data['worldPoint']['regionX']), int(data['worldPoint']['regionY']), int(
			data['worldPoint']['regionID'])

	def get_camera_position(self) -> Union[dict, None]:
		'''
		Fetches the position of a player's camera.
		Returns:
			A dict containing the player's camera position {yaw, pitch, x, y, z, x2, y2, z2},
		'''
		try:
			data = self.__do_get(endpoint=self.events_endpoint)
		except SocketError as e:
			print(e)
			return None

		return data['camera']

	def get_mouse_position(self) -> Union[Tuple[int, int], None]:
		'''
		Fetches the position of a player's mouse.
		Returns:
			A tuple of ints representing the player's mouse position (x, y),
			or None if an error occurred.
		'''
		try:
			data = self.__do_get(endpoint=self.events_endpoint)
		except SocketError as e:
			print(e)
			return None

		return int(data['mouse']['x']), int(data['mouse']['y'])

	def get_interaction_code(self) -> Union[int, None]:
		'''
		TODO: Figure out what the use case of this code is...
		'''
		try:
			data = self.__do_get(endpoint=self.events_endpoint)
		except SocketError as e:
			print(e)
			return None

		return int(data['interacting code'])

	def get_npc_name(self) -> Union[int, None]:
		'''
		TODO: Figure out what the use case of this code is...
		'''
		try:
			data = self.__do_get(endpoint=self.events_endpoint)
		except SocketError as e:
			print(e)
			return None

		return int(data['npc name'])

	def get_npc_health(self) -> Union[int, None]:
		'''
		TODO: Figure out what the use case of this code is...
		'''
		try:
			data = self.__do_get(endpoint=self.events_endpoint)
		except SocketError as e:
			print(e)
			return None

		return int(data['npc health'])

	def get_if_item_in_inv(self, item_id: int) -> Union[bool, None]:
		'''
		Checks if an item is in the inventory or not
		Args:
			item_id: the id of the item to check for
		Returns:
			True if the item is in the inventory, False if not, or None if an error occurred.
		'''
		try:
			data = self.__do_get(endpoint=self.inv_endpoint)
		except SocketError as e:
			print(e)
			return None

		return any(inventory_slot['id'] == item_id for inventory_slot in data)

	def find_item_in_inv(self, item_id: int) -> Union[List[Tuple[int, int]], None]:
		'''
		Finds an item in the inventory and returns a list of tuples containing the slot and quantity.
		Args:
			item_id: the id of the item to check for
		Returns:
			A list of tuples containing the slot and quantity of the item [(index, quantity), ...],
			or None if an error occurred.
		'''
		try:
			data = self.__do_get(endpoint=self.inv_endpoint)
		except SocketError as e:
			print(e)
			return None

		return [(index, inventory_slot['quantity']) for index, inventory_slot in enumerate(data) if inventory_slot['id'] == item_id]

	def get_player_equipment(self) -> Union[List[int], None]:
		'''
			Currently just gets the ID of the equipment until there is an easier way to convert ID to readable name
			-1 = nothing
			Returns: [helmet, cape, neck, weapon, chest, shield, legs, gloves, boots, ring, arrow]

			NOTE: Socket may be bugged with -1's in the middle of the data even all equipment slots are filled
		'''
		try:
			data = self.__do_get(endpoint=self.equip_endpoint)
		except SocketError as e:
			print(e)
			return None

		return [equipment_id['id'] for equipment_id in data]

	def convert_player_position_to_pixels(self):
		'''
		Convert a world point into coordinate where to click with the mouse to make it possible to move via the socket.
		TODO: Implement.
		'''
		pass
