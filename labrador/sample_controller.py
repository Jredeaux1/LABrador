########
# Name: sample_controller
#
# Purpose: A sample Pupper controller. Will move the robot around a bit then stop.
#
# Author: Prof. Riek <lriek@ucsd.edu>
#
# Date: 30 April 2024
#
# Prof. Riek Notes: Feel free to use this as starter code for the rest of the lab.
#####################

#Imports for voice recognition 
import speech_recognition as sr
import os

# Audio player library
import pygame

# Our custom interface, GoPupper. This specifies the message type (commands).
from pupper_interfaces.srv import GoPupper

# Packages to let us create nodes and spin them up
import rclpy
from rclpy.node import Node

#Imports from touch test
import RPi.GPIO as GPIO
import time

#Imports from display test
from MangDang.mini_pupper.display import Display, BehaviorState
import time
from resizeimage import resizeimage  # library for image resizing
from PIL import Image, ImageDraw, ImageFont # library for image manip.

MAX_WIDTH = 320   # max width of the LCD display

###
# Method: Sample Controller Async
# Purpose: Constructor for the controler
#
######
class SampleControllerAsync(Node):

    def __init__(self):
        # initalize
        super().__init__('sample_controller')
        self.cli = self.create_client(GoPupper, 'pup_command')

        # Check once per second if service matching the name is available 
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')

        # Create a new request object.
        self.req = GoPupper.Request()

        # Create display
        self.disp = Display()

        # There are 4 areas for touch actions
        # Each GPIO to each touch area
        self.touchPin_Front = 6
        self.touchPin_Left  = 3
        self.touchPin_Right = 16
        self.touchPin_Back  = 2
        
         # Initialize audio engine (pygame mixer)
        pygame.mixer.init()

        self.img_address = "/home/ubuntu/ros2_ws/src/labrador/my_images"
        self.sound_address = "/home/ubuntu/ros2_ws/src/labrador/sounds"

         # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Use GPIO number but not PIN number
        GPIO.setmode(GPIO.BCM)

        # Set up GPIO numbers to input
        GPIO.setup(self.touchPin_Front, GPIO.IN)
        GPIO.setup(self.touchPin_Left,  GPIO.IN)
        GPIO.setup(self.touchPin_Right, GPIO.IN)
        GPIO.setup(self.touchPin_Back,  GPIO.IN)

    ###
    # Name: send_move_request
    # Purpose: send_move_request method, send request and spin until receive response or fail
    # Arguments:  self (reference the current class), move_command (the command we plan to send to the server)
    #####
    def send_move_request(self, move_command):
        self.req = GoPupper.Request()
        self.req.command = move_command
        # Debug - uncomment if needed
        #print("In send_move_request, command is: %s" % self.req.command)
        self.future = self.cli.call_async(self.req)  # send the command to the server
        rclpy.spin_until_future_complete(self, self.future)
        return self.future.result()

    ###
    # Name
    #
    ####
    def play_bark(self):
        sound_file = self.sound_address + "/minecraft-dog-bark.mp3"
        pygame.mixer.music.load(sound_file)
        pygame.mixer.music.play()
        self.show_face(self.img_address+"/dogplayful.jpeg")
        while pygame.mixer.music.get_busy(): 
            time.sleep(0.1)
        
    def process_command(self, command):
        commands = {
            "speak": self.play_bark,
            "dance": self.pupper_conga_dance
        }
        if command in commands:
            commands[command]()
        else:
            print("Unknown command:", command)

    def listen_for_commands(self):
        while True:
            with self.microphone as source:
                print("Listening...")
                audio = self.recognizer.listen(source)
            try:
                command = self.recognizer.recognize_google(audio).lower()
                print("Command:", command)
                self.process_command(command)
            
            except sr.UnknownValueError:
                print("Could not understand audio")
    ###
    # Name: pupper_conga_dance
    # Purpose: Try to make the robot do the Conga (salsa), as per Gloria Estefan. We don't
    #          have a robot choreopgraher here so we'll just do our best.
    # Arguments:  self (reference the current class) -- /not sure if needed, but won't hurt/
    #####
    def pupper_conga_dance(self):
        # go left a few times
        for i in range(2):
            self.send_move_request("move_left")

        # go right a few times
        for i in range(2):
            self.send_move_request("move_right")

        # go backward 
        for i in range(3):
            self.send_move_request("move_backward")

        # go forward
        for i in range(3):
            self.send_move_request("move_forward")
   
    #def# Open the image (Your image file name goes here)
    #Copied code over from display test 
    def show_face(self,imgLoc): 
        imgFile = Image.open(imgLoc)

        # Convert to RGBA if needed
        if (imgFile.format == 'PNG'):
            if (imgFile.mode != 'RGBA'):
                imgOld = imgFile.convert("RGBA")
                imgFile = Image.new('RGBA', imgOld.size, (255, 255, 255))

        # We likely also need to resize to the pupper LCD display size (320x240).
        # Note, this is sometimes a little buggy, but you can get the idea. 
        width_size = (MAX_WIDTH / float(imgFile.size[0]))
        imgFile = resizeimage.resize_width(imgFile, MAX_WIDTH)

        newFileLoc = self.img_address + "/eyes.png"   #rename as you like

        # now output it (super inefficient, but it is what it is)
        imgFile.save(newFileLoc, imgFile.format)

        # Display it on Pupper's LCD dis
        self.disp.show_image(newFileLoc)

    def task4(self):
        while True:
            touchValue_Front = GPIO.input(self.touchPin_Front)
            touchValue_Back = GPIO.input(self.touchPin_Back)
            touchValue_Left = GPIO.input(self.touchPin_Left)
            touchValue_Right = GPIO.input(self.touchPin_Right)

            display_string = ''

            if not touchValue_Front:
                display_string += ' Front'
                self.send_move_request("move_forward")
                self.show_face(self.img_address+"/forwardeyes.png")

            if not touchValue_Back:
                display_string += ' Back'
                self.send_move_request("move_backward")
                self.show_face(self.img_address+"/downeyes.png")

            if not touchValue_Right:
                display_string += ' Right'
                self.send_move_request("move_right")
                self.show_face(self.img_address+"/righteyes.jpg")

            if not touchValue_Left:
                display_string += ' Left'
                self.send_move_request("move_left")
                self.show_face(self.img_address+"/lefteyes.png")

            if display_string == '':
                display_string = 'No button touched'
                self.show_face(self.img_address+"/sleepyeyes.jpg")

            print(display_string)

            time.sleep(0.5)

    def pupper_comm_test(self):
        # go left a few times
        for i in range(2):
            self.send_move_request("sit")

        # go right a few times
        for i in range(2):
            self.send_move_request("unsit")

        # go backward 
        for i in range(2):
            self.send_move_request("lay_down")

        # go forward
        for i in range(2):
            self.send_move_request("stand_up")
   

###
# Name: Main
# Purpose: Main function. Going to try to have the robot dance salsa. 
#####
def main():
    rclpy.init()
    sample_controller = SampleControllerAsync()
    
    # start listening to voice commands on a loop
    sample_controller.listen_for_commands() 

    # send commands to do the conga dance
    sample_controller.pupper_comm_test()

    # This spins up a client node, checks if it's done, throws an exception of there's an issue
    # (Probably a bit redundant with other code and can be simplified. But right now it works, so ¯\_(ツ)_/¯)
    while rclpy.ok():
        rclpy.spin_once(sample_controller)
        if sample_controller.future.done():
            try:
                response = sample_controller.future.result()
            except Exception as e:
                sample_controller.get_logger().info(
                    'Service call failed %r' % (e,))
            else:
                sample_controller.get_logger().info(
                   'Result of command: %s ' %
                   (response))
            break

    # Destroy node and shut down
    sample_controller.destroy_node()
    rclpy.shutdown()
    
    #from display test
    self.disp = Display()
    self.MAX_WIDTH = 320

if __name__ == '__main__':
    main()
