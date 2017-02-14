import gs
plus = gs.GetPlus()

mixer_channel = None


def update_clap(gui):
	global mixer_channel
	if plus.KeyDown(gs.InputDevice.KeyN):
		gui.Text("Clap !!")
		if mixer_channel is None:
			mixer_channel = plus.GetMixer().Stream("plugins/vcr/beep-1-sec.wav")
	else:
		if mixer_channel is not None:
			plus.GetMixer().StopAll()
			mixer_channel = None
