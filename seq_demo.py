from psychopy import core, event, visual
import numpy as np
import yaml
from ExoDisplay import ExoDisplay

class SequenceGame:

    def __init__(self, config='default'):
        # load config
        self.config = yaml.load(open('config/'+config+'.yml'),Loader=yaml.FullLoader)

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
            self.key_codes = ['q','w','e','r','v','n','u','i','o','p']

        self.run_msg_text = 'Run {} of {}'
        self.exp_end_text = 'All done!'
        self.run_msg = visual.TextStim(win=self.win,
            text='', pos=(0,-0.2),
            color=self.exo_display.cue_color,
            height=0.08)

        # sequence learning variables
        self.trial_clock = core.Clock()
        self.start_clock = core.Clock()
        self.hand = 'left'
        self.trial_stage = 'cue' # ['cue', 'press', 'feedback']
        self.seq_in_trial = 0
        self.START_WAIT_TIME = self.config['start_wait_time']
        self.SEQ_PER_TRIAL = self.config['seq_per_trial']
        self.CUE_TIME = self.config['cue_time']
        self.FEEDBACK_TIME = self.config['feedback_time']
        self.ITI_TIME = self.config['iti_time']
        self.NUM_RUNS = self.config['num_runs']
        self.TRIALS_PER_RUN = self.config['trials_per_run']
        self.SEQUENCES = self.config['sequences']
        self.trial_num = 0
        self.run_num = 0
        self.trial_base_order = ['a','b']
        self.trial_order = np.tile(self.trial_base_order,
            int(self.TRIALS_PER_RUN/len(self.trial_base_order)))
        self.set_sequence()
        self.reset_for_start()

    def set_sequence(self):
        next_seq = self.SEQUENCES[self.trial_order[self.trial_num]]
        self.exo_display.cue_display.active_hand = next_seq['hand']
        self.sequence = np.array(next_seq['seq'])

    def reset_for_start(self, hand='left'):
        self.exp_stage = 'wait'
        if self.run_num < self.NUM_RUNS:
            self.run_msg.text = self.run_msg_text.format(self.run_num+1,self.NUM_RUNS)
        else:
            self.run_msg.text = self.exp_end_text
        self.exo_display.cue_display.set_for_start(hand)
        for key in self.exo_display.key_stims:
            key.setBaseColor(self.exo_display.cue_color)
        self.start_keys_pressed = np.full(self.exo_display.num_fingers, False)
        self.start_initiated = False

    def wait_for_start(self):
        self.run_msg.draw()
        for pressed_key in np.where(self.exo_display.keydowns==True)[0]:
            self.start_keys_pressed[pressed_key] = True
            self.exo_display.key_stims[pressed_key].setBaseColor(self.exo_display.success_color)

        if ((sum(self.start_keys_pressed)>=self.exo_display.num_active_fingers)
                and not(self.start_initiated)):
            self.start_initiated = True
            self.start_clock.reset()

        if self.start_initiated and self.start_clock.getTime()>self.START_WAIT_TIME:
            if self.run_num < self.NUM_RUNS:
                self.reset_for_exp()
            else:
                self.quit()

    def reset_for_exp(self):
        self.exp_stage = 'run'
        self.reset_for_trial()

    def reset_for_trial(self):
        self.set_sequence()
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
                seq=str(self.sequence+1)[1:-1])
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
                self.trial_num += 1
                if self.trial_num >= self.TRIALS_PER_RUN:
                    self.trial_num = 0
                    self.run_num += 1
                    self.reset_for_start()
                else:
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
