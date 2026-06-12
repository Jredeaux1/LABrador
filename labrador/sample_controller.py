########
# Name: sample_controller
#
# Purpose: Main controller for LABrador. Listens for voice input
#          and coordinates movement, facial display, and audio
#          feedback to create an interactive companion robot.
#
# Author: JayLynne Redeaux (Jredeaux@ucsd.edu) & Mack Markham (mmarkham@ucsd.edu) 
#
# Date: 11, June 2026
#####################

#Imports for voice recognition 
import speech_recognition as sr
import os

# Audio player library
import pygame

# Our custom interface, GoPupper. This specifies the message type (commands).
from pupper_interfaces.srv import GoPupper

from geometry_msgs.msg import Pose

# Packages to let us create nodes and spin them up
import rclpy
from rclpy.node import Node


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
        self.pose_pub = self.create_publisher(Pose, '/body_pose', 10)

        # Create display
        self.disp = Display()
        
        # Initialize audio engine (pygame mixer)
        pygame.mixer.init()

        self.img_address = "/home/ubuntu/ros2_ws/src/labrador/my_images"
        self.sound_address = "/home/ubuntu/ros2_ws/src/labrador/sounds"

        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()


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
    # Name: play_bark
    # Purpose: Have the robot output a bark MP3 audio 
    # Arguments:  
    #     self    - reference to the current SampleControllerAsync object
    ####
    def play_bark(self):
        sound_file = self.sound_address + "/minecraft-dog-bark.mp3"
        pygame.mixer.music.load(sound_file)
        pygame.mixer.music.play()
        self.show_face(self.img_address+"/dogplayful.jpeg")
        while pygame.mixer.music.get_busy(): 
            time.sleep(0.1)
    ###
    # Name: spin_around
    # Purpose: Have the robot spin as best as it can 
    # Arguments: 
    #     self    - reference to the current SampleControllerAsync object
    ####
    def spin_around(self):
        pose = Pose()
        pose.orientation.w = 1.0
        self.pose_pub.publish(pose)
        self.show_face(self.img_address+"/dogplayful.jpeg")
        time.sleep(3)
        for i in range(30):
            self.send_move_request("turn_left")
    ###
    # Name: play_dead
    # Purpose: Have the robot "play dead" which combines
    # turning the screen to a skull image and laying down
    # Arguments:  
    #     self    - reference to the current SampleControllerAsync object
    ####
    def play_dead(self): 
        self.show_face(self.img_address+"/skull.png") 
        pose = Pose()
        pose.position.z = -0.55
        pose.orientation.w = 1.0
        self.pose_pub.publish(pose) 

    ###
    # Name: sit_down
    # Purpose: Have the robot sit (Rear legs crouching) 
    # face is turned to the playful dog image again
    # Arguments:  
    #     self    - reference to the current SampleControllerAsync object
    ####
    def sit_down(self): 
        self.show_face(self.img_address+"/dogplayful.jpeg") 
        pose = Pose()
        pose.position.z = -0.04
        pose.orientation.y = -0.15
        pose.orientation.w = 0.98
        self.pose_pub.publish(pose)
        
    ###
    # Name: lay_down
    # Purpose: Have the robot lay down (all legs crouching) 
    # face is turned to the playful dog image again
    # Arguments:  
    ####
    def lay_down(self): 
        self.show_face(self.img_address+"/dogplayful.jpeg")         
        pose = Pose()
        pose.position.z = -0.55
        pose.orientation.w = 1.0
        self.pose_pub.publish(pose)
        
    ###
    # Name: stand_up
    # Purpose: Have the robot stand back up, called after lay/sit/play_dead 
    # face is turned to the playful dog image again
    # Arguments:  self (reference the current class)
    ####
    def stand_up(self):
        self.show_face(self.img_address+"/dogplayful.jpeg")
        pose = Pose()
        pose.orientation.w = 1.0
        self.pose_pub.publish(pose)

    ###
    # Name: process_command
    # Purpose: Matches a recognized voice command to its corresponding
    #          robot behavior and executes the associated function.
    # Arguments:
    #     self    - reference to the current SampleControllerAsync object
    #     command - string containing the recognized voice command
    ####
    def process_command(self, command):
        commands = {
            "speak": self.play_bark,
            "dance": self.pupper_conga_dance,
            "down": self.sit_down,
            "flat": self.lay_down,
            "dead": self.play_dead,
            "spin": self.spin_around,
            "stand": self.stand_up
        }
        if command in commands:
            commands[command]()
        else:
            print("Unknown command:", command)
    ###
    # Name: listen_for_commands
    # Purpose: Continuously listens for spoken user commands, converts
    #          speech to text using Google's Speech Recognition API,
    #          and passes recognized commands to the command processor.
    # Arguments:
    #     self - reference to the current SampleControllerAsync object
    ####
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
        self.show_face(self.img_address+"/dogplayful.jpeg")
        pose = Pose()
        pose.orientation.w = 1.0
        self.pose_pub.publish(pose)

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

   
###
# Name: Main
# Purpose: Main function.  
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
