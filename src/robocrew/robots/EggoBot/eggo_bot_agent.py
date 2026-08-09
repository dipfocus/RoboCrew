from robocrew.core.LLMAgent import LLMAgent
from robocrew.core.tools import create_say
import queue
from pathlib import Path

class EggoBotAgent(LLMAgent):
	"""EggoBot specific LLM agent that inherits from base LLMAgent."""
	def __init__(
		self,
		model: str,
		tools: list,
		servo_controler,
		name: str | None = None,
		thinking_level: str | None = None,
		camera_fov: int = 90,
		history_len: int | None = None,
		use_memory: bool = False,
		main_camera=None,
		sounddevice_index_or_alias=None,
		wakeword: str | None = None,
		tts: bool = False,
	):
		self.sounddevice_index_or_alias = sounddevice_index_or_alias
		self.sound_receiver = None
		self.speech_queue = None
		self.user_text = None

		if self.sounddevice_index_or_alias is not None:
			# import here to avoid importing sounddevice and its dependencies when not needed
			from robocrew.core.sound_receiver import SoundReceiver
			self.speech_queue = queue.Queue()
			self.sound_receiver = SoundReceiver(
				self.sounddevice_index_or_alias,
				self.speech_queue,
				wakeword,
			)

		system_prompt = Path(__file__).with_name("eggobot.prompt").read_text(encoding="utf-8")

		if tts:
			tools.append(create_say(self.sound_receiver))
			system_prompt += (
				" You can speak to the user using the `say` tool. "
				"Use it to communicate important updates, greet users, or answer their questions verbally."
			)

		super().__init__(
			model=model,
			tools=tools,
			main_camera=main_camera,
			name=name,
			system_prompt=system_prompt,
			thinking_level=thinking_level,
			camera_fov=camera_fov,
			history_len=history_len,
			use_memory=use_memory
		)
		self.servo_controler = servo_controler
		self.servo_controler.reset_head_position()

	def check_for_new_speech(self):
		"""Non-blockingly checks the speech queue for one heard utterance."""
		if self.sounddevice_index_or_alias and self.speech_queue and not self.speech_queue.empty():
			return self.speech_queue.get()
		return None

	def extra_loop_content(self):
		content = []
		if self.sounddevice_index_or_alias and self.user_text:
			content.append({"type": "text", "text": f"\n\nUser said: '{self.user_text}'"})
			self.user_text = None
			self.idle = True
		return content

	def check_for_new_input(self):
		user_text = self.check_for_new_speech()
		if user_text:
			self.user_text = user_text
			return True
		return False

	def cleanup(self):
		print("Disconnecting servo controller...")
		self.servo_controler.disconnect()
