from psychopy import core, event, visual
import numpy as np
import yaml
from ExoDisplay import ExoDisplay

class SequenceGame:

    def __init__(self, config='default'):
        # load config
        self.config = yaml.load(open('config/'+config+'.yml'),Loader=yaml.FullLoader)

        # load hand/finger params
        self.num_hands = self.config['num_hands']
        self.fingers_per_hand = self.config['fingers_per_hand']
        self.num_fingers = self.num_hands * self.fingers_per_hand 

        # set display 
        self.win = visual.Window(size=(self.config['screen_width'], self.config['screen_height']),
                                 color=self.config['bg_color'], units='height')
        self.exo_display = ExoDisplay(self.win, config=config)

        # add key controls
        event.globalKeys.add(key='q', modifiers=['ctrl'], func=self.quit)
        # event.globalKeys.add(key='o', func=self.exo_display.key_stims[0].setBaseColor, func_kwargs=dict(color=[-0.5,-0.5,-0.5]))
        # event.globalKeys.add(key='s', modifiers=['ctrl'], func=self.toggle_exp)

        if not(self.exo_display.exo_active):
            from psychopy.iohub.client import launchHubServer
            self.io = launchHubServer()
            self.kb = self.io.devices.keyboard
            self.key_codes = ['a','w','e','r','b']

        # sequence learning constants 
        self.DEMO_SEQUENCE = np.array([4,2,3,1,0])
        self.DEMO_SEQUENCE_2 = np.array([1,3,2,4,0])
        self.START_WAIT_TIME = 0.3 # seconds

        # XXX FIGURE OUT TIMINGS/TRIAL DESIGN
        self.CUE_TIME = 1.0 # seconds
        self.END_WAIT_TIME = 0.5 # seconds
        self.start_msg_text = 'Press All Keys To Begin'
        self.start_msg = visual.TextStim(win=self.win,
            text=self.start_msg_text, pos=(0,0.25),
            color=self.exo_display.cue_color,
            height=0.05)

        # sequence learning variables
        self.trial_clock = core.Clock()
        self.start_clock = core.Clock()
        self.reset_for_start()
        self.sequence = self.DEMO_SEQUENCE
        self.hand = 'left'
        self.best_times = np.full(len(self.sequence), 1.0)
        self.trial_stage = 'cue' # ['cue', 'press', 'feedback']
        self.seq_in_trial = 0
        self.SEQ_PER_TRIAL = self.config['seq_per_trial']
        self.CUE_TIME = self.config['cue_time']
        self.FEEDBACK_TIME = self.config['feedback_time']
        self.ITI_TIME = self.config['iti_time']

    def reset_for_start(self):
        self.exp_stage = 'wait'
        for key in self.exo_display.key_stims:
            key.setBaseColor(self.exo_display.cue_color)
        self.start_keys_pressed = np.full(self.exo_display.num_fingers, False)
        self.start_initiated = False

    def wait_for_start(self):
        self.start_msg.draw()
        for pressed_key in np.where(self.exo_display.keydowns==True)[0]:
            self.start_keys_pressed[pressed_key] = True
            self.exo_display.key_stims[pressed_key].setBaseColor(self.exo_display.success_color)

        if all(self.start_keys_pressed) and not(self.start_initiated):
            self.start_initiated = True
            self.start_clock.reset()

        if self.start_initiated and self.start_clock.getTime()>self.START_WAIT_TIME:
            self.reset_for_exp()

    def reset_for_exp(self):
        self.exp_stage = 'run'
        self.reset_for_trial()

    def reset_for_trial(self):
        self.seq_in_trial = 0
        self.trial_stage = 'cue'
        self.trial_clock.reset()
        self.reset_for_seq()

    def reset_for_seq(self):
        for key in self.exo_display.key_stims:
            key.setBaseColor(self.exo_display.key_color)
        self.key_num_to_press = 0
        self.key_to_press = self.sequence[0]
        self.correct_in_seq = np.full(len(self.sequence),False)

    def reset_new_keydowns(self):
        self.exo_display.new_keydowns[:] = False

    def run_trial(self):
        self.exo_display.cue_display.draw()
        if self.trial_stage == 'cue':
            self.exo_display.cue_display.set_cue(
                seq=str(self.sequence+1)[1:-1], hand=self.hand)
            if self.trial_clock.getTime() > self.CUE_TIME:
                self.trial_stage = 'press'
                self.exo_display.cue_display.set_all_idle()
                self.reset_new_keydowns()
        elif self.trial_stage == 'press':
            self.key_to_press = self.sequence[self.key_num_to_press]
            self.exo_display.key_stims[self.key_to_press].setBaseColor(self.exo_display.cue_color)
            if any(self.exo_display.new_keydowns):
                pressed_key = np.where(self.exo_display.new_keydowns==True)[0][0]
                if pressed_key == self.key_to_press:
                    self.correct_in_seq[self.key_num_to_press] = True
                    self.exo_display.key_stims[self.key_to_press].setBaseColor(self.exo_display.success_color)
                else:
                    self.correct_in_seq[self.key_num_to_press] = False
                    self.exo_display.key_stims[self.key_to_press].setBaseColor(self.exo_display.fail_color)
                self.key_num_to_press += 1
                self.exo_display.new_keydowns[:] = False
                if self.key_num_to_press >= len(self.sequence):
                    self.trial_stage = 'feedback'
                    if all(self.correct_in_seq):
                        self.exo_display.cue_display.set_feedback('success')
                    else:
                        self.exo_display.cue_display.set_feedback('fail')
                    self.trial_clock.reset()
                    self.seq_in_trial+=1
        elif self.trial_stage == 'feedback':
            if self.trial_clock.getTime() > self.FEEDBACK_TIME:
                self.exo_display.cue_display.set_all_idle()
                if self.seq_in_trial < self.SEQ_PER_TRIAL:
                    self.reset_for_seq()
                    self.trial_stage = 'press'
                else:
                    self.trial_stage = 'iti'
                    self.trial_clock.reset()
                    self.reset_for_seq()
        elif self.trial_stage == 'iti':
            if self.trial_clock.getTime() > self.ITI_TIME:
                if all(self.sequence == self.DEMO_SEQUENCE):
                    self.sequence = self.DEMO_SEQUENCE_2
                else:
                    self.sequence = self.DEMO_SEQUENCE
                if self.hand == 'left':
                    self.hand = 'right'
                else:
                    self.hand = 'left'
                self.reset_for_trial()

    def check_keys(self):
        events = self.kb.getKeys()
        for kbe in events:
            if kbe.key in self.key_codes:
                if kbe.type == 'KEYBOARD_PRESS':
                    self.exo_display.spoof_keydowns[int(np.where(kbe.key==np.array(self.key_codes))[0])]=True
                elif kbe.type == 'KEYBOARD_RELEASE':
                    self.exo_display.spoof_keydowns[int(np.where(kbe.key==np.array(self.key_codes))[0])]=False

    def run_main_loop(self):
        while True:
            if not(self.exo_display.exo_active):
                self.check_keys()
            self.exo_display.update_inputs()
            if self.exp_stage == 'wait':
                self.wait_for_start()
            elif self.exp_stage == 'run':
                self.run_trial()
            self.exo_display.draw()
            self.win.flip()

    def quit(self):
        if self.exo_display.exo_active:
            self.exo_display.exo.stop()
        core.quit()

if __name__ == '__main__':
    game = SequenceGame()
    game.run_main_loop()
