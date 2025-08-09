"""
Global Mouse Click and Key Press Counter
Counts left and right clicks anywhere on your screen, plus ESC, F1-F4 keys.

Requirements:
    pip install pynput
"""

import math
import tkinter as tk
from tkinter import ttk
from pynput import mouse, keyboard
import time

class GlobalClickKeyCounter:
    def __init__(self, root):
        self.root = root
        self.root.title("Runescape APM calculator")
        self.root.geometry("515x550")
        
        # Make window stay on top (optional)
        self.root.attributes('-topmost', True)
        
        # Initialize counters
        self.left_clicks = 0
        self.right_clicks = 0
        self.middle_clicks = 0
        self.esc_presses = 0
        self.f1_presses = 0
        self.f2_presses = 0
        self.f3_presses = 0
        self.f4_presses = 0
        self.ctrl_presses = 0
        self.shift_presses = 0
        self.scroll_presses = 0
        self.total_actions = 0
        self.current_apm = 0
        
        self.monitoring = False
        self.mouse_listener = None
        self.keyboard_listener = None
        self.keys_held = set()  # Track keys currently held down
        self.last_scroll_time = 0
        self.scroll_cooldown = 0.4  # seconds
        
        # Initialize monitoring pulse icon
        self.pulse_job = None  
        self.pulse_state = True
        
        # Initialize timer
        self.start_time = None
        self.timer_job = None 
        self.elapsed = 0
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weight
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Status indicator
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.grid(row=1, column=0, pady=10)
        
        self.status_indicator = tk.Canvas(self.status_frame, width=20, height=20)
        self.status_indicator.grid(row=0, column=0, padx=5)
        self.status_circle = self.status_indicator.create_oval(2, 2, 18, 18, 
                                                               fill='red', 
                                                               outline='darkred')
        
        self.status_label = ttk.Label(self.status_frame, text="Not Monitoring", 
                                     font=('Arial', 14))
        self.status_label.grid(row=0, column=1)
        
        # Total actions display
        self.total_actions_label = ttk.Label(self.status_frame, text="Total Actions: 0", 
                                    font=('Arial', 14, 'bold'), 
                                    foreground='darkblue')
        self.total_actions_label.grid(row=0, column=2, padx=5)

        # Timer display
        self.timer_label = ttk.Label(self.status_frame, text="Time: 00:00", 
                                    font=('Arial', 14, 'bold'), 
                                    foreground='black')
        self.timer_label.grid(row=0, column=3, padx=5)

        
        # Mouse clicks section
        mouse_frame = ttk.LabelFrame(main_frame, text="Mouse Clicks", padding="10")
        mouse_frame.grid(row=2, column=0, pady=10, sticky=(tk.W, tk.E))
        mouse_frame.columnconfigure(0, weight=1)
        mouse_frame.columnconfigure(1, weight=1)
        mouse_frame.columnconfigure(2, weight=1)
        
        # Left click counter
        left_frame = ttk.Frame(mouse_frame)
        left_frame.grid(row=0, column=0, padx=15)
        ttk.Label(left_frame, text="Left Clicks:",font=('Arial', 12)).grid(row=0, column=0)
        self.left_label = ttk.Label(left_frame, text="0", font=('Arial', 24, 'bold'), foreground='blue')
        self.left_label.grid(row=1, column=0)

        # Middle click counter
        middle_frame = ttk.Frame(mouse_frame)
        middle_frame.grid(row=0, column=1, padx=15)
        ttk.Label(middle_frame, text="Wheel Clicks:", font=('Arial', 12)).grid(row=0, column=0)
        self.middle_label = ttk.Label(middle_frame, text="0", font=('Arial', 24, 'bold'),foreground='darkgreen')
        self.middle_label.grid(row=1, column=0)
        
        # Right click counter
        right_frame = ttk.Frame(mouse_frame)
        right_frame.grid(row=0, column=2, padx=15)
        ttk.Label(right_frame, text="Right Clicks:", font=('Arial', 12)).grid(row=0, column=0)
        self.right_label = ttk.Label(right_frame, text="0", font=('Arial', 24, 'bold'), foreground='red')
        self.right_label.grid(row=1, column=0)
    
        # Key presses section
        key_frame = ttk.LabelFrame(main_frame, text="Key Presses", padding="10")
        key_frame.grid(row=3, column=0, pady=10, sticky=(tk.W, tk.E))
        
        # Configure key frame columns
        for i in range(5):
            key_frame.columnconfigure(i, weight=1)
        
        # ESC key counter
        esc_frame = ttk.Frame(key_frame)
        esc_frame.grid(row=0, column=0, padx=5)
        ttk.Label(esc_frame, text="ESC:", font=('Arial', 10)).grid(row=0, column=0)
        self.esc_label = ttk.Label(esc_frame, text="0", 
                                  font=('Arial', 16, 'bold'), 
                                  foreground='purple')
        self.esc_label.grid(row=1, column=0)
        
        # F1-F4 key counters
        self.f_labels = {}
        f_colors = ['orange', 'green', 'brown', 'navy']
        
        for i, (key, color) in enumerate(zip(['F1', 'F2', 'F3', 'F4'], f_colors)):
            f_frame = ttk.Frame(key_frame)
            f_frame.grid(row=0, column=i+1, padx=5)
            ttk.Label(f_frame, text=f"{key}:", font=('Arial', 10)).grid(row=0, column=0)
            self.f_labels[key] = ttk.Label(f_frame, text="0", 
                                          font=('Arial', 16, 'bold'), 
                                          foreground=color)
            self.f_labels[key].grid(row=1, column=0)

        #TODO ADD QOL tracking clicks
        #Left/right shift same shifter copunter
        #left right control same ctrl counter
        #Scroll wheel in and out one action per zoom in or out, doesnt matter how zoomed in or out it is 
        # QOL Key presses section
        qol_key_frame = ttk.LabelFrame(main_frame, text="QOL Key Presses", padding="10")
        qol_key_frame.grid(row=4, column=0, pady=10, sticky=(tk.W, tk.E))
        qol_key_frame.columnconfigure(0, weight=1)
        qol_key_frame.columnconfigure(1, weight=1)
        qol_key_frame.columnconfigure(2, weight=1)

        # CTRL key counter
        ctrl_frame = ttk.Frame(qol_key_frame)
        ctrl_frame.grid(row=0, column=0, padx=5)
        ttk.Label(ctrl_frame, text="CTRL:", font=('Arial', 10)).grid(row=0, column=0)
        self.ctrl_label = ttk.Label(ctrl_frame, text="0",font=('Arial', 16, 'bold'), foreground='black')
        self.ctrl_label.grid(row=1, column=0)

        # SHIFT key counter
        shift_frame = ttk.Frame(qol_key_frame)
        shift_frame.grid(row=0, column=1, padx=5)
        ttk.Label(shift_frame, text="SHIFT:", font=('Arial', 10)).grid(row=0, column=0)
        self.shift_label = ttk.Label(shift_frame, text="0", font=('Arial', 16, 'bold'), foreground='yellow')
        self.shift_label.grid(row=1, column=0)

        # wheel SCROLL key counter
        scroll_frame = ttk.Frame(qol_key_frame)
        scroll_frame.grid(row=0, column=2, padx=5)
        ttk.Label(scroll_frame, text="SCROLL:", font=('Arial', 10)).grid(row=0, column=0)
        self.scroll_label = ttk.Label(scroll_frame, text="0", font=('Arial', 16, 'bold'), foreground='grey')
        self.scroll_label.grid(row=1, column=0)

        # Display current APM
        self.current_apm_label = ttk.Label(main_frame, text="Click start monitoring to begin calculating APM", 
                               font=('Arial', 14, 'bold'))
        self.current_apm_label.grid(row=5, column=0, pady=(0, 5))

        # Control buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, pady=5)
        
        self.start_button = ttk.Button(button_frame, text="Start Monitoring", 
                                       command=self.toggle_monitoring,
                                       width=15)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.reset_button = ttk.Button(button_frame, text="Reset Counters", 
                                       command=self.reset_counters,
                                       width=15)
        self.reset_button.grid(row=0, column=1, padx=5)
        
        # Instructions
        instructions = ttk.Label(main_frame, 
                                text="Click 'Start Monitoring' then click anywhere or press ESC/F1-F4.\n" +
                                     "The window will stay on top to show counts in real-time.",
                                font=('Arial', 10), 
                                foreground='gray')
        instructions.grid(row=7, column=0, pady=(5, 0))
        
        # Last action display
        self.action_label = ttk.Label(main_frame, text="Last action: None", 
                                     font=('Arial', 9), foreground='gray')
        self.action_label.grid(row=8, column=0, pady=(5, 0))
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_click(self, x, y, button, pressed):
        """Handle mouse click events"""
        if not pressed:  # Only count on button release
            return
        # Update counters in main thread
        if button == mouse.Button.left:
            self.root.after(0, self.increment_left)
            self.root.after(0, lambda: self.update_action(f"Left click at ({int(x)}, {int(y)})"))
        elif button == mouse.Button.right:
            self.root.after(0, self.increment_right)
            self.root.after(0, lambda: self.update_action(f"Right click at ({int(x)}, {int(y)})"))
        elif button == mouse.Button.middle:
            self.root.after(0, self.increment_middle)
            self.root.after(0, lambda: self.update_action(f"Wheel click at ({int(x)}, {int(y)})"))

    def on_scroll(self, x, y, dx, dy):
        """Handle mouse scroll events"""
        now = time.time()

        # Only count if enough time passed since last scroll
        if now - self.last_scroll_time >= self.scroll_cooldown:
            self.last_scroll_time = now

            if dy > 0:
                self.root.after(0, self.increment_scroll)
                self.root.after(0, lambda: self.update_action(f"Scrolled up at ({int(x)}, {int(y)})"))
            elif dy < 0:
                self.root.after(0, self.increment_scroll)
                self.root.after(0, lambda: self.update_action(f"Scrolled down at ({int(x)}, {int(y)})"))
    
    def on_key_press(self, key):
        """Handle key press events without counting held keys multiple times"""
        if key in self.keys_held:
            return  # Ignore if key is already held

        self.keys_held.add(key)

        try:
            # Handle special keys
            if key == keyboard.Key.esc:
                self.root.after(0, self.increment_esc)
                self.root.after(0, lambda: self.update_action("ESC key pressed"))
            elif key == keyboard.Key.f1:
                self.root.after(0, self.increment_f1)
                self.root.after(0, lambda: self.update_action("F1 key pressed"))
            elif key == keyboard.Key.f2:
                self.root.after(0, self.increment_f2)
                self.root.after(0, lambda: self.update_action("F2 key pressed"))
            elif key == keyboard.Key.f3:
                self.root.after(0, self.increment_f3)
                self.root.after(0, lambda: self.update_action("F3 key pressed"))
            elif key == keyboard.Key.f4:
                self.root.after(0, self.increment_f4)
                self.root.after(0, lambda: self.update_action("F4 key pressed"))
            elif key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                self.root.after(0, self.increment_ctrl)
                self.root.after(0, lambda: self.update_action("CTRL key pressed"))
            elif key in (keyboard.Key.shift_l, keyboard.Key.shift_r):
                self.root.after(0, self.increment_shift)
                self.root.after(0, lambda: self.update_action("SHIFT key pressed"))
        except AttributeError:
            pass
    
    def on_key_release(self, key):
        """Mark key as released so it can be counted again"""
        if key in self.keys_held:
            self.keys_held.remove(key)
    
    def increment_left(self):
        """Increment left click counter"""
        self.left_clicks += 1
        self.left_label.config(text=str(self.left_clicks))
        # Flash effect
        self.left_label.config(foreground='cyan')
        self.root.after(100, lambda: self.left_label.config(foreground='blue'))
        # Update the total actions counter + ui
        self.update_total_actions_ui()
    
    def increment_right(self):
        """Increment right click counter"""
        self.right_clicks += 1
        self.right_label.config(text=str(self.right_clicks))
        # Flash effect
        self.right_label.config(foreground='pink')
        self.root.after(100, lambda: self.right_label.config(foreground='red'))
        # Update the total actions counter + ui
        self.update_total_actions_ui()
    
    def increment_middle(self):
        """Increment middle/wheel click counter"""
        self.middle_clicks += 1

        self.middle_label.config(text=str(self.middle_clicks))
        # Flash effect
        self.middle_label.config(foreground='lightgreen')
        self.root.after(100, lambda: self.middle_label.config(foreground='darkgreen'))
        # Update the total actions counter + ui
        self.update_total_actions_ui()
    
    def increment_middle(self):
        """Increment middle/wheel click counter"""
        self.middle_clicks += 1
        self.middle_label.config(text=str(self.middle_clicks))
        # Flash effect
        self.middle_label.config(foreground='lightgreen')
        self.root.after(100, lambda: self.middle_label.config(foreground='darkgreen'))
        # Update the total actions counter + ui
        self.update_total_actions_ui()
    
    def increment_esc(self):
        """Increment ESC key counter"""
        self.esc_presses += 1
        self.esc_label.config(text=str(self.esc_presses))
        # Flash effect
        self.esc_label.config(foreground='magenta')
        self.root.after(100, lambda: self.esc_label.config(foreground='purple'))
        # Update the total actions counter + ui
        self.update_total_actions_ui()
    
    def increment_f1(self):
        """Increment F1 key counter"""
        self.f1_presses += 1
        self.f_labels['F1'].config(text=str(self.f1_presses))
        # Flash effect
        self.f_labels['F1'].config(foreground='yellow')
        self.root.after(100, lambda: self.f_labels['F1'].config(foreground='orange'))
        # Update the total actions counter + ui
        self.update_total_actions_ui()
    
    def increment_f2(self):
        """Increment F2 key counter"""
        self.f2_presses += 1
        self.f_labels['F2'].config(text=str(self.f2_presses))
        # Flash effect
        self.f_labels['F2'].config(foreground='lightgreen')
        self.root.after(100, lambda: self.f_labels['F2'].config(foreground='green'))
        # Update the total actions counter + ui
        self.update_total_actions_ui()
    
    def increment_f3(self):
        """Increment F3 key counter"""
        self.f3_presses += 1
        self.f_labels['F3'].config(text=str(self.f3_presses))
        # Flash effect
        self.f_labels['F3'].config(foreground='tan')
        self.root.after(100, lambda: self.f_labels['F3'].config(foreground='brown'))
        # Update the total actions counter + ui
        self.update_total_actions_ui()
    
    def increment_f4(self):
        """Increment F4 key counter"""
        self.f4_presses += 1
        self.f_labels['F4'].config(text=str(self.f4_presses))
        # Flash effect
        self.f_labels['F4'].config(foreground='lightblue')
        self.root.after(100, lambda: self.f_labels['F4'].config(foreground='navy'))
        # Update the total actions counter + ui
        self.update_total_actions_ui()

    def increment_ctrl(self):
        """Increment either ctrl key counter"""
        self.ctrl_presses += 1
        self.ctrl_label.config(text = str(self.ctrl_presses))
        # Flash effect
        self.ctrl_label.config(foreground='grey')
        self.root.after(100, lambda: self.ctrl_label.config(foreground='black'))
        # Update the total actions counter + ui
        self.update_total_actions_ui()

    def increment_shift(self):
        """Increment either shift key counter"""
        self.shift_presses += 1
        self.shift_label.config(text = str(self.shift_presses))
        # Flash effect
        self.shift_label.config(foreground='orange')
        self.root.after(100, lambda: self.shift_label.config(foreground='yellow'))
        # Update the total actions counter + ui
        self.update_total_actions_ui()

    def increment_scroll(self):
        """Increment wheel scroll counter"""
        self.scroll_presses += 1
        self.scroll_label.config(text = str(self.scroll_presses))
        # Flash effect
        self.scroll_label.config(foreground='black')
        self.root.after(100, lambda: self.scroll_label.config(foreground='grey'))
        # Update the total actions counter + ui
        self.update_total_actions_ui()

    def update_action(self, action_text):
        """Update last action display"""
        self.total_actions += 1
        self.action_label.config(text=f"Last action: {action_text}")

    def update_total_actions_ui(self):
        """update the total actions counter"""
        self.total_actions_label.config(text=f"Total Actions: {str(self.total_actions +1)}")
        """calculate the current APM after each increment change"""
        if self.elapsed > 1:
            self.current_apm = math.floor((self.total_actions/math.floor(self.elapsed))*60)
            self.current_apm_label.config(text=f"Actions Per Minute: {str(self.current_apm)}")
    
    def toggle_monitoring(self):
        """Start or stop monitoring mouse clicks and key presses"""
        if not self.monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """Start monitoring mouse clicks and key presses globally"""
        self.monitoring = True
        self.start_button.config(text="Stop Monitoring")
        self.status_label.config(text="Monitoring Active")
        self.status_indicator.itemconfig(self.status_circle, fill='green', 
                                        outline='darkgreen')
        
        # Start the pulsing animation
        self.start_pulse_animation()
        
        # Start the timer
        self.start_timer()
        
        # Start mouse listener in a separate thread
        self.mouse_listener = mouse.Listener(on_click=self.on_click, on_scroll=self.on_scroll)
        self.mouse_listener.start()
        
        # Start keyboard listener in a separate thread
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
        self.keyboard_listener.start()
    
    def stop_monitoring(self):
        """Stop monitoring mouse clicks and key presses"""
        self.monitoring = False
        self.start_button.config(text="Start Monitoring")
        self.status_label.config(text="Not Monitoring")
        
        # Stop the pulsing animation
        self.stop_pulse_animation()
        
        # Stop the timer
        self.stop_timer()
        
        self.status_indicator.itemconfig(self.status_circle, fill='red', 
                                        outline='darkred')
        
        # Stop listeners
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
            
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
    
    def start_pulse_animation(self):
        """Start smooth pulsing animation for the status indicator"""
        self.pulse_state = True
        self.pulse_smooth()
    
    def pulse_smooth(self):
        """Create a smooth pulsing effect by gradually changing opacity/brightness"""
        if not self.monitoring:
            return
            
        # Create gradient of green colors for smooth pulse
        colors = [
            ('#90EE90', '#228B22'),  # Light green
            ('#7FDD7F', '#1F7A1F'),
            ('#6ECC6E', '#1C691C'), 
            ('#5DBB5D', '#195819'),
            ('#4CAA4C', '#164716'),
            ('#3B993B', '#133613'),
            ('#2A882A', '#102510'),
            ('#19771A', '#0D140D'),
            ('#228B22', '#0A0F0A'),  # Dark green
            ('#2A882A', '#102510'),
            ('#3B993B', '#133613'),
            ('#4CAA4C', '#164716'),
            ('#5DBB5D', '#195819'),
            ('#6ECC6E', '#1C691C'),
            ('#7FDD7F', '#1F7A1F'),
        ]
        
        # Get current color index based on time
        color_index = int(time.time() * 8) % len(colors)  # 8 changes per second
        fill_color, outline_color = colors[color_index]
        
        self.status_indicator.itemconfig(self.status_circle, 
                                       fill=fill_color, 
                                       outline=outline_color)
        
        # Schedule next frame (about 60 FPS)
        self.pulse_job = self.root.after(16, self.pulse_smooth)

    def stop_pulse_animation(self):
        """Stop the pulsing animation"""
        if self.pulse_job:
            self.root.after_cancel(self.pulse_job)
            self.pulse_job = None
    
    def start_timer(self):
        """Start the monitoring timer"""
        self.start_time = time.time()
        self.update_timer()
    
    def stop_timer(self):
        """Stop the monitoring timer"""
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
    
    def update_timer(self):
        """Update the timer display"""
        if not self.monitoring or self.start_time is None:
            return
        
        self.elapsed = time.time() - self.start_time
        minutes = int(self.elapsed // 60)
        seconds = int(self.elapsed % 60)

        self.timer_label.config(text=f"Time: {minutes:02d}:{seconds:02d}")
        
        # Schedule next update in 1 second
        self.timer_job = self.root.after(1000, self.update_timer)

    def reset_counters(self):
        """Reset all counters to zero"""
        self.left_clicks = 0
        self.right_clicks = 0
        self.middle_clicks = 0
        self.esc_presses = 0
        self.f1_presses = 0
        self.f2_presses = 0
        self.f3_presses = 0
        self.f4_presses = 0
        self.ctrl_presses = 0
        self.shift_presses = 0
        self.scroll_presses = 0
        self.total_actions = 0
        self.elapsed = 0
        self.current_apm = 0
        self.keys_held.clear()
        
        self.left_label.config(text="0")
        self.right_label.config(text="0")
        self.middle_label.config(text="0")
        self.esc_label.config(text="0")
        for key in ['F1', 'F2', 'F3', 'F4']:
            self.f_labels[key].config(text="0")
        self.ctrl_label.config(text="0")
        self.shift_label.config(text="0")
        self.scroll_label.config(text="0")
        self.action_label.config(text="Last action: None")

        # Ypdate timer ui
        self.timer_label.config(text="Time: 00:00")
        # Update the total actions counter ui
        self.total_actions_label.config(text=str("Total Actions: 0"))
        # Update current_apm_label
        self.current_apm_label.config(text="Click start monitoring to begin calculating APM")
    
    def on_closing(self):
        """Handle window closing event"""
        self.stop_monitoring()
        self.root.destroy()

def main():    
    root = tk.Tk()
    app = GlobalClickKeyCounter(root)
    root.mainloop()

if __name__ == "__main__":
    main()