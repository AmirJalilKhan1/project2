from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.pickers import MDDatePicker
from kivy.clock import Clock
from plyer import filechooser, storagepath
import sqlite3
import os
from PIL import Image

# Initialize SQLite database
conn = sqlite3.connect('users.db')
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    full_name TEXT,
    dob TEXT,
    password TEXT
)
''')
conn.commit()

def int_to_bin(value):
    """Convert an integer to a binary (string) format."""
    return '{0:08b}'.format(value)

def bin_to_int(binary):
    """Convert a binary (string) format to an integer."""
    return int(binary, 2)

def merge_bits(cover_bits, secret_bits):
    """Merge the cover and secret bits."""
    return cover_bits[:4] + secret_bits[:4]

def embed_image(cover_img_path, secret_img_path):
    cover_img = Image.open(cover_img_path).convert('RGB')
    secret_img = Image.open(secret_img_path).convert('RGB')

    cover_pixels = cover_img.load()
    secret_pixels = secret_img.load()

    secret_img_width, secret_img_height = secret_img.size

    # Embed the dimensions of the secret image into the first few pixels of the cover image
    cover_pixels[0, 0] = (secret_img_width // 256, secret_img_width % 256, cover_pixels[0, 0][2])
    cover_pixels[0, 1] = (secret_img_height // 256, secret_img_height % 256, cover_pixels[0, 1][2])

    for y in range(secret_img_height):
        for x in range(secret_img_width):
            cover_pixel = cover_pixels[x, y + 2]
            secret_pixel = secret_pixels[x, y]
            cover_r, cover_g, cover_b = int_to_bin(cover_pixel[0]), int_to_bin(cover_pixel[1]), int_to_bin(cover_pixel[2])
            secret_r, secret_g, secret_b = int_to_bin(secret_pixel[0]), int_to_bin(secret_pixel[1]), int_to_bin(secret_pixel[2])
            merged_r, merged_g, merged_b = merge_bits(cover_r, secret_r), merge_bits(cover_g, secret_g), merge_bits(cover_b, secret_b)
            cover_pixels[x, y + 2] = (bin_to_int(merged_r), bin_to_int(merged_g), bin_to_int(merged_b))

    gallery_path = storagepath.get_pictures_dir()
    output_path = os.path.join(gallery_path, "stego_image.png")
    cover_img.save(output_path, 'PNG')
    print(f"Image embedded successfully! Saved as {output_path}")

def extract_bits(merged_bits):
    """Extract the secret bits from the merged bits."""
    return merged_bits[4:] + '0000'

def extract_image(stego_img_path):
    stego_img = Image.open(stego_img_path).convert('RGB')
    stego_pixels = stego_img.load()

    secret_img_width = stego_pixels[0, 0][0] * 256 + stego_pixels[0, 0][1]
    secret_img_height = stego_pixels[0, 1][0] * 256 + stego_pixels[0, 1][1]

    extracted_img = Image.new('RGB', (secret_img_width, secret_img_height))
    extracted_pixels = extracted_img.load()

    for y in range(secret_img_height):
        for x in range(secret_img_width):
            stego_pixel = stego_pixels[x, y + 2]
            stego_r, stego_g, stego_b = int_to_bin(stego_pixel[0]), int_to_bin(stego_pixel[1]), int_to_bin(stego_pixel[2])
            secret_r, secret_g, secret_b = extract_bits(stego_r), extract_bits(stego_g), extract_bits(stego_b)
            extracted_pixels[x, y] = (bin_to_int(secret_r), bin_to_int(secret_g), bin_to_int(secret_b))

    gallery_path = storagepath.get_pictures_dir()
    output_path = os.path.join(gallery_path, "extracted_image.png")
    extracted_img.save(output_path, 'PNG')
    print(f"Secret image extracted successfully! Saved as {output_path}")

def hide_text(image_path, output_path, text):
    img = Image.open(image_path)
    img = img.convert('RGB')
    binary_text = ''.join(format(ord(char), '08b') for char in text) + '1111111111111110'
    binary_text_index = 0
    pixels = img.load()

    for y in range(img.height):
        for x in range(img.width):
            if binary_text_index >= len(binary_text):
                break

            r, g, b = pixels[x, y]
            r = (r & ~1) | int(binary_text[binary_text_index])
            binary_text_index += 1

            if binary_text_index < len(binary_text):
                g = (g & ~1) | int(binary_text[binary_text_index])
                binary_text_index += 1

            if binary_text_index < len(binary_text):
                b = (b & ~1) | int(binary_text[binary_text_index])
                binary_text_index += 1

            pixels[x, y] = (r, g, b)

        if binary_text_index >= len(binary_text):
            break

    img.save(output_path)
    print("Text hidden in image successfully! Saved as {}".format(output_path))

def extract_text(image_path):
    img = Image.open(image_path)
    binary_data = ""
    pixels = img.load()

    for y in range(img.height):
        for x in range(img.width):
            r, g, b = pixels[x, y]
            binary_data += str(r & 1)
            binary_data += str(g & 1)
            binary_data += str(b & 1)

            if '1111111111111110' in binary_data:
                binary_data = binary_data[:binary_data.index('1111111111111110')]
                break
        else:
            continue
        break

    text = ''.join(chr(int(binary_data[i:i + 8], 2)) for i in range(0, len(binary_data), 8))
    print("Extracted Text:", text)
    return text

# Define missing screen classes
class SplashScreen(Screen):
    """Intro splash screen that shows SecureTalk logo or name"""

    def on_enter(self):
        Clock.schedule_once(self.switch_to_home, 4)  # Show splash for 4 seconds

    def switch_to_home(self, dt):
        self.manager.current = "login"

class LoginScreen(Screen):
    pass

class SignUpScreen(Screen):
    pass

class HomeScreen(Screen):
    pass

class TextInputBox(MDBoxLayout):
    """Custom input dialog for text embedding (Updated Version)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = "20dp"  # Adds spacing
        self.padding = ["10dp", "-25dp", "10dp", "-25dp"]  # Moves the input box down
        self.text_field = MDTextField(
            hint_text="Enter your text",
            size_hint_y=None,
            height="40dp",
            pos_hint={"center_x": 0.5},  # Centers the text box
            foreground_color=[0, 0, 0, 1],  # Set the text color to black
            color_mode='custom',  # Use custom color mode
            line_color_focus=[0, 0, 0, 1]  # Set the line color when focused to black
        )
        self.add_widget(self.text_field)


class SecureTalkApp(MDApp):
    selected_date = ""

    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(SignUpScreen(name="signup"))
        sm.add_widget(HomeScreen(name="home"))
        return Builder.load_file('securetalk.kv')

    def login(self):
        """Login system"""
        username = self.root.get_screen("login").ids.login_username.text
        password = self.root.get_screen("login").ids.login_password.text

        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()

        if user:
            self.root.current = "home"
        else:
            self.show_dialog("Login Failed", "Invalid username or password!")

    def signup(self):
        """Signup system with unique username check"""
        username = self.root.get_screen("signup").ids.signup_username.text
        full_name = self.root.get_screen("signup").ids.signup_fullname.text
        dob = self.selected_date
        password = self.root.get_screen("signup").ids.signup_password.text

        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()

        if user:
            self.show_dialog("Signup Failed", "Username already taken!")
        else:
            c.execute("INSERT INTO users (username, full_name, dob, password) VALUES (?, ?, ?, ?)",
                      (username, full_name, dob, password))
            conn.commit()
            self.show_dialog("Signup Successful", "Account created successfully!")
            self.root.current = "login"

    def show_date_picker(self):
        """Opens a calendar widget to select Date of Birth"""
        date_dialog = MDDatePicker()
        date_dialog.bind(on_save=self.set_date)
        date_dialog.open()

    def set_date(self, instance, value, date_range):
        """Sets the selected Date of Birth"""
        self.selected_date = str(value)
        self.root.get_screen("signup").ids.signup_dob.text = self.selected_date

    def text_embedding(self):
        filechooser.open_file(on_selection=self.store_cover_image)

    def store_cover_image(self, selection):
        if selection:
            self.cover_image = selection[0]
            self.show_text_input()

    def show_text_input(self):
        """Show a text input dialog with updated text field position."""
        self.text_input_box = TextInputBox()

        self.dialog = MDDialog(
            title="Enter Text to Hide",
            type="custom",
            content_cls=self.text_input_box,
            buttons=[MDRaisedButton(text="OK", on_release=self.text_selected, text_color=[0, 0, 0, 1])],
            # Set button text color to black
        )
        self.dialog.open()

    def text_selected(self, instance):
        """Embed text inside an image and prevent duplicate operations."""
        text = self.text_input_box.text_field.text
        hide_text(self.cover_image, "stego_text.png", text)
        self.dialog.dismiss()  # Close the dialog after one execution
        self.show_dialog("Success", "Text embedded successfully!")

    def text_extraction(self):
        filechooser.open_file(on_selection=self.extract_text_from_image)

    def extract_text_from_image(self, selection):
        if selection:
            extracted_text = extract_text(selection[0])
            self.show_dialog("Extracted Text", extracted_text)

    def image_embedding(self):
        filechooser.open_file(on_selection=self.store_image_cover)

    def store_image_cover(self, selection):
        if selection:
            self.cover_image = selection[0]
            filechooser.open_file(on_selection=self.store_secret_image)

    def store_secret_image(self, selection):
        if selection:
            self.secret_image = selection[0]
            embed_image(self.cover_image, self.secret_image)
            self.show_dialog("Success", "Image embedded successfully!")

    def image_extraction(self):
        filechooser.open_file(on_selection=self.extract_hidden_image)

    def extract_hidden_image(self, selection):
        if selection:
            extract_image(selection[0])
            self.show_dialog("Success", "Image extracted successfully!")

    def show_dialog(self, title, message):
        dialog = MDDialog(title=title, text=message)
        dialog.open()

if __name__ == "__main__":
    SecureTalkApp().run()