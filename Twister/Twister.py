from __future__ import with_statement


import Live
import time
import math
from itertools import chain
from _Framework.ButtonElement import ButtonElement
from _Framework.ButtonMatrixElement import ButtonMatrixElement
from _Framework.ChannelStripComponent import ChannelStripComponent
from _Framework.ClipSlotComponent import ClipSlotComponent
from _Framework.CompoundComponent import CompoundComponent
from _Framework.ControlElement import ControlElement
from _Framework.ControlSurface import ControlSurface
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.DeviceComponent import DeviceComponent
from _Framework.DisplayDataSource import DisplayDataSource
from _Framework.EncoderElement import EncoderElement
from _Framework.InputControlElement import *
from _Framework.MixerComponent import MixerComponent
from VCM600.MixerComponent import MixerComponent
from _Framework.ModeSelectorComponent import ModeSelectorComponent
from _Framework.NotifyingControlElement import NotifyingControlElement
from _Framework.SceneComponent import SceneComponent
from _Framework.SessionComponent import SessionComponent
from _Framework.SessionZoomingComponent import DeprecatedSessionZoomingComponent as SessionZoomingComponent
from _Framework.SliderElement import SliderElement
from _Framework.TransportComponent import TransportComponent
from _Framework.ModesComponent import AddLayerMode, LayerMode, MultiEntryMode, ModesComponent, SetAttributeMode, ModeButtonBehaviour, CancellableBehaviour, AlternativeBehaviour, ReenterBehaviour, DynamicBehaviourMixin, ExcludingBehaviourMixin, ImmediateBehaviour, LatchingBehaviour, ModeButtonBehaviour
from _Framework.Layer import Layer
from _Framework.SubjectSlot import SubjectEvent, subject_slot, subject_slot_group
from _Framework.Task import *
from _Framework.ComboElement import ComboElement, DoublePressElement, MultiElement, DoublePressContext

#from _Mono_Framework.MonoBridgeElement import MonoBridgeElement
#from _Mono_Framework.MonoBridgeElement import MonoBridgeElement
#from _Mono_Framework.TranslationComponent import TranslationComponent
#from _Mono_Framework.MonoEncoderElement import MonoEncoderElement
#from _Mono_Framework.MonoButtonElement import MonoButtonElement
from _Mono_Framework.DetailViewControllerComponent import DetailViewControllerComponent
#from _Mono_Framework.LiveUtils import *
#from _Mono_Framework.ModDevices import *
#from _Mono_Framework.Mod import *
#from _Mono_Framework.MonoDeviceComponent import MonoDeviceComponent
#from _Mono_Framework.Debug import *
from _Mono_Framework.DeviceNavigator import *
from _Mono_Framework._deprecated.AutoArmComponent import AutoArmComponent

from _Generic.Devices import *
from Map import *


session = None
mixer = None

MIDI_NOTE_TYPE = 0
MIDI_CC_TYPE = 1
MIDI_PB_TYPE = 2
MIDI_MSG_TYPES = (MIDI_NOTE_TYPE, MIDI_CC_TYPE, MIDI_PB_TYPE)
#MIDI_NOTE_ON_STATUS = 144
#MIDI_NOTE_OFF_STATUS = 128
#MIDI_CC_STATUS = 176
#MIDI_PB_STATUS = 224

#INC_DEC = [-1, 1]



#class CancellableBehaviourWithRelease(CancellableBehaviour):
#
#
#	def release_delayed(self, component, mode):
#		component.pop_mode(mode)
	

#	def update_button(self, component, mode, selected_mode):
#		button = component.get_mode_button(mode)
#		groups = component.get_mode_groups(mode)
#		selected_groups = component.get_mode_groups(selected_mode)
#		value = (mode == selected_mode or bool(groups & selected_groups))*10 or 3
#		button.send_value(value, True)
	

class SpecialMixerComponent(MixerComponent):
	' Special mixer class that uses return tracks alongside midi and audio tracks'
	__module__ = __name__


	def __init__(self, *a, **k):
		self._is_locked = False #added
		super(SpecialMixerComponent, self).__init__(*a, **k)
	

	def on_selected_track_changed(self):
		selected_track = self.song().view.selected_track
		if selected_track != None:
			if (self._selected_strip != None):
				if self._is_locked == False: #added
					self._selected_strip.set_track(selected_track)
			if self.is_enabled():
				if (self._next_track_button != None):
					if (selected_track != self.song().master_track):
						self._next_track_button.turn_on()
					else:
						self._next_track_button.turn_off()
				if (self._prev_track_button != None):
					if (selected_track != self.song().tracks[0]):
						self._prev_track_button.turn_on()
					else:
						self._prev_track_button.turn_off()		  
	

	def tracks_to_use(self):
		return tuple(self.song().visible_tracks) + tuple(self.song().return_tracks)


class Twister(ControlSurface):
	__module__ = __name__
	__doc__ = ' Twister controller script '


	def __init__(self, c_instance):
		super(Twister, self).__init__(c_instance)
		self._host_name = 'Ohm'
		self._color_type = 'OhmRGB'
		#self._rgb = 1
		#self._timer = 0
		#self._touched = 0
		#self.flash_status = 1
		#self._backlight = 127
		#self._backlight_type = 'static'
		#self._ohm = 127
		#self._ohm_type = 'static'
		self._device_selection_follows_track_selection = True
		#self._keys_octave = 5
		#self._keys_scale = 0
		#self._tempo_buttons = None
		with self.component_guard():
			self._setup_controls()
			self._setup_transport_control()
			self._setup_clip_control()
			self._setup_autoarm()
			self._setup_mixer_control()
			self._setup_session_control()
			self._setup_device_control()
			#self._setup_mod()
			#self._setup_modes()
			self._assign_page_constants()
			self._last_device = None
			self.song().view.add_selected_track_listener(self._update_selected_device)
			self.show_message('Twister Control Surface Loaded')
		#if FORCE_TYPE is True:
		#	self._rgb = FORCE_COLOR_TYPE
		#else:
		#	self.schedule_message(10, self.query_ohm, None)
		self.log_message('<<<<<<<<<<<<<<<<<<<<<<<<< Twister log opened >>>>>>>>>>>>>>>>>>>>>>>>>')
	


	#def update_display(self):
	#	super(Twister, self).update_display()
	#	self._timer = (self._timer + 1) % 256
		#self.flash()
		#self.strobe()

	

	def get_device_bank(self):
		return self._device._bank_index
	

	def _setup_controls(self):
		is_momentary = True
		self._fader = [ None for index in range(8) ]
		self._sec = [ None for index in range(8) ]
		self._dial = [ None for index in range(24) ]
		self._devicedial = [ None for index in range(8) ]
		self._button = [ None for index in range(8) ]
		self._solo = [ None for index in range(8) ]
		self._arm = [ None for index in range(8) ]
		self._mute = [ None for index in range(8) ]
		self._menu = [ None for index in range(8) ]
		self._devices = [ None for index in range(8) ]
		for index in range(8):
			self._fader[index] = EncoderElement(MIDI_CC_TYPE, CHANNEL, OHM_FADERS[index], Live.MidiMap.MapMode.absolute)
		
		for index in range(8):
			self._sec[index] = EncoderElement(MIDI_CC_TYPE, CHANNEL, SEC_FADERS[index], Live.MidiMap.MapMode.absolute)		
		
		for index in range(8):
			self._button[index] = ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL+1, OHM_BUTTONS[index])
		for index in range(8):
			self._solo[index] = ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL+1, OHM_SOLO[index])
		for index in range(8):
			self._arm[index] = ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL+1, OHM_ARM[index])
		for index in range(8):
			self._mute[index] = ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL+1, OHM_MUTE[index])
			
		for index in range(24):
			self._dial[index] = EncoderElement(MIDI_CC_TYPE, CHANNEL, OHM_DIALS[index], Live.MidiMap.MapMode.absolute)
		
		for index in range(8):
			self._devicedial[index] = EncoderElement(MIDI_CC_TYPE, CHANNEL, OHM_DEVICE_DIALS[index], Live.MidiMap.MapMode.absolute)

		self._knobs = []
		for index in range(8):
			self._knobs.append(self._devicedial[index])

		for index in range(8):
			self._menu[index] = ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL+1, OHM_MENU[index])
			
		
		for index in range(8):
			self._devices[index] = ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL+1, OHM_DEVICE[index])


		self._nav_l = ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL+3, NAV_L)
		self._nav_r = ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL+3, NAV_R)
		
		#self._livid = ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL+9, LIVID)
		#self._shift_l = ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL+9, SHIFT_L)
		#self._shift_r = ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL+9, SHIFT_R)
		self._matrix = ButtonMatrixElement()
		self._matrix.name = 'Matrix'
		self._grid = [ None for index in range(8) ]
		self._monomod = ButtonMatrixElement()
		self._monomod.name = 'Monomod'
		for column in range(8):
			self._grid[column] = [ None for index in range(8) ]
			for row in range(8):
				self._grid[column][row] = ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL+9, column * 8 + row, 'Grid_' + str(column) + '_' + str(row), self)

		for row in range(8):
			button_row = []
			for column in range(7):
				button_row.append(self._grid[column][row])

			self._matrix.add_row(tuple(button_row))

		for row in range(8):
			button_row = []
			for column in range(8):
				button_row.append(self._grid[column][row])

			self._monomod.add_row(tuple(button_row))

		self._dial_matrix = ButtonMatrixElement()
		for row in range(3):
			dial_row = []
			for column in range(4):
				dial_row.append(self._dial[column + (row*4)])

			self._dial_matrix.add_row(tuple(dial_row))

		self._menu_matrix = ButtonMatrixElement([self._menu])
		self._devices_matrix = ButtonMatrixElement([self._devices])


	def _setup_clip_control(self)
		self._clip_control = ClipSlotComponent()
		self._clip_control.name = 'Clip Control'

	def _setup_transport_control(self):
		self._transport = TransportComponent()
		self._transport.name = 'Transport'
		#self._transport.layer = Layer(priority = 4, play_button = self._menu[2], stop_button = self._menu[3])
	
	def _setup_autoarm(self):
		self._auto_arm = AutoArmComponent(name='Auto_Arm')
		self._auto_arm.can_auto_arm_track = self._can_auto_arm_track
	def _can_auto_arm_track(self, track):
		routing = track.current_input_routing
		return routing == 'Ext: All Ins' or routing == 'All Ins'

	def _setup_mixer_control(self):
		global mixer
		is_momentary = True
		self._num_tracks = 8
		mixer = MixerComponent(8, 0, True, True)
		mixer.name = 'Mixer'
		self._mixer = mixer
		for index in range(8):
			mixer.channel_strip(index).set_volume_control(self._fader[index])
			mixer.channel_strip(index).set_solo_button(self._solo[index])
			mixer.channel_strip(index).set_arm_button(self._arm[index])
			mixer.channel_strip(index).set_mute_button(self._mute[index])
		selected_strip = self._mixer.selected_strip()
		selected_strip.set_invert_mute_feedback(True)
		
		self.song().view.selected_track = mixer.channel_strip(0)._track
	

	def _setup_session_control(self):
		global session
		is_momentary = True
		num_tracks = 8
		num_scenes = 1
		session = SessionComponent(num_tracks, num_scenes)
		session.name = 'Session'
		self._session = session
		session.set_offsets(0, 0)
		self._scene = [ None for index in range(1) ]
		for row in range(num_scenes):
			self._scene[row] = session.scene(row)
			self._scene[row].name = 'Scene_' + str(row)
			for column in range(num_tracks):
				clip_slot = self._scene[row].clip_slot(column)
				clip_slot.name = str(column) + '_Clip_Slot_' + str(row)

		session.set_mixer(self._mixer)
		session.set_show_highlight(True)
		self._session_zoom = SessionZoomingComponent(session)
		self._session_zoom.name = 'Session_Overview'
		self.set_highlighting_session_component(self._session)

	

	def _setup_device_control(self):
		self._device = DeviceComponent()
		self._device.name = 'Device_Component'
		self.set_device_component(self._device)
		
		self._device_navigator = DetailViewControllerComponent()
		self._device_navigator.name = 'Device_Navigator'
		
		self._device_nav = DeviceNavigator(self._device, self._mixer, self)
		self._device_nav.name = 'Device_Navigators'
		self._device_selection_follows_track_selection = True

	def device_follows_track(self, val):
		self._device_selection_follows_track_selection = val == 1
		return self


	def disconnect(self):
		"""clean things up on disconnect"""
		self.song().view.remove_selected_track_listener(self._update_selected_device)
		self.log_message(time.strftime('%d.%m.%Y %H:%M:%S', time.localtime()) + '--------------= Twister log closed =--------------')
		super(Twister, self).disconnect()
		#rebuild_sys()
	

	def _get_num_tracks(self):
		return self.num_tracks
	
	def _assign_page_constants(self):
		with self.component_guard():
			self._session_zoom.set_zoom_button(self._grid[7][7])
			self._session_zoom.set_button_matrix(self._matrix)
			self._session.set_track_bank_buttons(self._nav_r, self._nav_l)
			for column in range(8):
				self._mixer.channel_strip(column).set_select_button(self._button[column])
				self._mixer.channel_strip(column).set_volume_control(self._fader[column])
				self._mixer.channel_strip(column).set_solo_button(self._solo[column])
				self._mixer.channel_strip(column).set_arm_button(self._arm[column])
				self._mixer.channel_strip(column).set_mute_button(self._mute[column])
				self._mixer.channel_strip(column).set_pan_control(self._dial[column])
				self._mixer.channel_strip(column).set_send_controls(tuple([self._dial[column+8], self._dial[column+16]]))
				
			self._mixer.master_strip().set_volume_control(self._sec[4])
			#self._mixer.master_strip().set_select_button(self._menu[7])
			self._mixer.set_prehear_volume_control(self._sec[5])
			
			self._mixer.selected_strip().set_volume_control(self._sec[0])
			self._mixer.selected_strip().set_pan_control(self._sec[1])
			self._mixer.selected_strip().set_send_controls([self._sec[2], self._sec[3]])
			
			self._mixer.set_select_buttons(self._menu[7], self._menu[3])
			
			self._mixer.selected_strip().set_mute_button(self._menu[0])
			self._mixer.selected_strip().set_arm_button(self._menu[2])
			self._mixer.selected_strip().set_solo_button(self._menu[1])
			

			### USING CLIP CONTROL OVER TRANSPORT CONTROL FOR NOW.  FOCUS IS LIVE DJ-ING
			self._clip_control.set_launch_button(self._menu[4])
			self._clip_control.set_stopped_value(self._menu[5])
			self._clip_control.set_record_button_value(self.menu[6])

			# self._transport.set_play_button(self._menu[4])
			# self._transport.set_stop_button(self._menu[5])



			#self._transport.set_loop_button(self._menu[4])
			#self._transport.set_overdub_button(self._menu[3])
			#self._transport.set_seek_buttons(self._menu[6], self._menu[5])
			self._transport.set_record_button(self._menu[6])
			#self._menu[0].send_value(PLAY_COLOR[self._rgb], True)
			#self._menu[0]._on_value = 48			
			#self._transport.set_tap_tempo_button(self._menu[3])
			#self._menu[2]._on_value = 48			
			#self._menu[2]._off_value = 0
			#self._menu[2].send_value(PLAY_COLOR[self._rgb], True)
			#self._menu[1]._off_value = 84
			#self._menu[1]._on_value = 84
			#self._menu[1].send_value(84, True)
			
			self._device_navigator.set_device_nav_buttons(self._devices[1], self._devices[2])
			#self._device_navigator.set_prev_button(self._devices[1])
			#self._device_navigator.set_prev_button(self._devices[2])
			
			#self._device_nav.set_chain_nav_buttons(self._devices[4], self._devices[7])
			self._device_nav.set_prev_chain_button(self._devices[4])
			self._device_nav.set_next_chain_button(self._devices[7])
			#self._device_nav.set_exit_button(self._devices[4])
			#self._device_nav.set_enter_button(self._devices[7])
			#self._device_nav.set_exit_button(self._devices[7])
			
			#self.devices[7].set_on_value(DEVICE_LOCK[self._rgb])					#set the on color for the Device lock encoder button
			self._device.set_lock_button(self._devices[3])							#assign encoder button 7 to the device lock control
			#self._devices[0].set_on_value(DEVICE_ON[self._rgb])						#set the on color for the Device on/off encoder button 
			self._device.set_on_off_button(self._devices[0])							#assing encoder button 4 to the device on/off control
			#for index in range(2):															#setup a recursion to generate indexes so that we can reference the correct controls to assing to the device_navigator functions
				#self._devices[index + 1].set_on_value(DEVICE_NAV_COLOR[self._rgb])			#assign the on color for the device navigator
				#self._encoder_button[index + 10].set_on_value(DEVICE_BANK[self._rgb])		#assign the on color for the device bank controls
			self._device.set_bank_nav_buttons(self._devices[5], self._devices[6]) 	#set the device components bank nav controls to encoder buttons 8 and 9
			self._transport.set_enabled(True)
			
		self._device.set_enabled(True)
		device_param_controls = []
		for index in range(8):
			device_param_controls.append(self._devicedial[index])

		self._device.set_parameter_controls(tuple(device_param_controls))


		#for index in range(8):
		#	self._devices[index]._on_value = 68
		self._device_navigator.set_enabled(True)
		self._transport.set_enabled(True)				
		#self.request_rebuild_midi_map()
			
		self._device.set_enabled(True)
		self._device_navigator.set_enabled(True)	
	
	def _get_devices(self, track):

		def dig(container_device):
			contained_devices = []
			if container_device.can_have_chains:
				for chain in container_device.chains:
					for chain_device in chain.devices:
						for item in dig(chain_device):
							contained_devices.append(item)
			else:
				contained_devices.append(container_device)
			return contained_devices
		

		devices = []
		for device in track.devices:
			for item in dig(device):
				devices.append(item)
				#self.log_message('appending ' + str(item))
		return devices	
	

	def _update_selected_device(self):
		if self._device_selection_follows_track_selection is True:
			self._update_device_selection()
	

	def to_encoder(self, num, val):
		rv = int(val * 127)
		self._device._parameter_controls[num].receive_value(rv)
		p = self._device._parameter_controls[num]._parameter_to_map_to
		newval = val * (p.max - p.min) + p.min
		p.value = newval

	def get_clip_names(self):
		clip_names = []
		for scene in self._session._scenes:
			for clip_slot in scene._clip_slots:
				if clip_slot.has_clip() is True:
					clip_names.append(clip_slot._clip_slot)
					return clip_slot._clip_slot

		return clip_names