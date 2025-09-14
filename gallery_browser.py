
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.uix.image import Image as KivyImage
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle

GALLERY_ROOT = 'gallery'


class ArrowIcons(Widget):
    """Widget to display navigation arrow icons."""
    def __init__(self, arrows, **kwargs):
        super().__init__(**kwargs)
        self.arrows = arrows  # set of 'up', 'down', 'left', 'right'
        self.size_hint = (None, None)
        self.size = (120, 120)
        self.pos_hint = {'right': 1, 'bottom': 1}
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        self.canvas_instructions = []
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(1, 1, 1, 0.7)
            # Draw arrows as simple triangles
            cx, cy = self.x + self.width/2, self.y + self.height/2
            s = 24
            if 'up' in self.arrows:
                self.draw_triangle(cx, cy+30, s, 'up')
            if 'down' in self.arrows:
                self.draw_triangle(cx, cy-30, s, 'down')
            if 'left' in self.arrows:
                self.draw_triangle(cx-30, cy, s, 'left')
            if 'right' in self.arrows:
                self.draw_triangle(cx+30, cy, s, 'right')

    def draw_triangle(self, cx, cy, s, direction):
        from kivy.graphics import Triangle
        if direction == 'up':
            Triangle(points=[cx-s/2, cy-s/2, cx+s/2, cy-s/2, cx, cy+s/2])
        elif direction == 'down':
            Triangle(points=[cx-s/2, cy+s/2, cx+s/2, cy+s/2, cx, cy-s/2])
        elif direction == 'left':
            Triangle(points=[cx+s/2, cy-s/2, cx+s/2, cy+s/2, cx-s/2, cy])
        elif direction == 'right':
            Triangle(points=[cx-s/2, cy-s/2, cx-s/2, cy+s/2, cx+s/2, cy])


class GalleryBrowser(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = 'albums'  # 'albums' or 'images'
        self.albums = sorted([d for d in os.listdir(GALLERY_ROOT) if os.path.isdir(os.path.join(GALLERY_ROOT, d))])
        self.album_idx = 0
        self.images = []
        self.image_idx = 0
        self.display = Label(text='', font_size=32, halign='center', valign='middle', color=(1,1,1,1))
        self.img_widget = KivyImage(allow_stretch=True, keep_ratio=True)
        self.arrow_widget = None
        Window.bind(on_key_down=self.on_key_down)
        self.update_view()

    def toggle_fullscreen(self):
        Window.fullscreen = not Window.fullscreen

    def update_view(self):
        self.clear_widgets()
        if self.state == 'albums':
            # Album selection: show album list, highlight selected, show image count, show up/down/right arrows
            if not self.albums:
                self.display.text = "No albums found"
                self.display.font_size = 32
                self.display.halign = 'center'
                self.display.valign = 'middle'
                self.display.color = (1,1,1,1)
                self.display.size_hint = (1,1)
                self.display.pos_hint = {'center_x':0.5, 'center_y':0.5}
                self.add_widget(self.display)
            else:
                lines = []
                for i, name in enumerate(self.albums):
                    album_path = os.path.join(GALLERY_ROOT, name)
                    img_count = len([f for f in os.listdir(album_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))])
                    prefix = "> " if i == self.album_idx else "  "
                    suffix = f"  ({img_count})"
                    lines.append(f"{prefix}{name}{suffix}")
                self.display.text = '\n'.join(lines)
                self.display.font_size = 32
                self.display.halign = 'left'
                self.display.valign = 'middle'
                self.display.color = (1,1,1,1)
                self.display.size_hint = (1,1)
                self.display.pos_hint = {'center_x':0.5, 'center_y':0.5}
                self.add_widget(self.display)
                # Add arrow icons (up/down/right)
                self.arrow_widget = ArrowIcons({'up','down','right'})
                self.arrow_widget.size_hint = (None, None)
                self.arrow_widget.size = (120, 120)
                self.arrow_widget.pos_hint = {'right':1, 'bottom':1}
                self.add_widget(self.arrow_widget)
        elif self.state == 'images':
            # Image view: show image fullscreen, no text, show up/down/left arrows
            if not self.images:
                self.display.text = "No images in album"
                self.display.font_size = 32
                self.display.halign = 'center'
                self.display.valign = 'middle'
                self.display.color = (1,1,1,1)
                self.display.size_hint = (1,1)
                self.display.pos_hint = {'center_x':0.5, 'center_y':0.5}
                self.add_widget(self.display)
                self.arrow_widget = ArrowIcons({'left'})
                self.arrow_widget.size_hint = (None, None)
                self.arrow_widget.size = (120, 120)
                self.arrow_widget.pos_hint = {'right':1, 'bottom':1}
                self.add_widget(self.arrow_widget)
            else:
                img_path = os.path.join(GALLERY_ROOT, self.albums[self.album_idx], self.images[self.image_idx])
                self.img_widget.source = img_path
                self.img_widget.allow_stretch = True
                self.img_widget.keep_ratio = True
                self.img_widget.size_hint = (1,1)
                self.img_widget.pos_hint = {'center_x':0.5, 'center_y':0.5}
                self.add_widget(self.img_widget)
                # Add arrow icons (up/down/left)
                self.arrow_widget = ArrowIcons({'up','down','left'})
                self.arrow_widget.size_hint = (None, None)
                self.arrow_widget.size = (120, 120)
                self.arrow_widget.pos_hint = {'right':1, 'bottom':1}
                self.add_widget(self.arrow_widget)

    def on_key_down(self, window, key, scancode, codepoint, modifier):
        # 'w' key toggles fullscreen (key==119)
        if key == 119:
            self.toggle_fullscreen()
            return
        if self.state == 'albums':
            if key == 273:  # Up arrow
                self.album_idx = (self.album_idx - 1) % len(self.albums) if self.albums else 0
                self.update_view()
            elif key == 274:  # Down arrow
                self.album_idx = (self.album_idx + 1) % len(self.albums) if self.albums else 0
                self.update_view()
            elif key in (275, 100):  # Right arrow or 'd'
                if self.albums:
                    album_path = os.path.join(GALLERY_ROOT, self.albums[self.album_idx])
                    self.images = sorted([
                        f for f in os.listdir(album_path)
                        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))
                    ])
                    self.image_idx = 0
                    self.state = 'images'
                    self.update_view()
        elif self.state == 'images':
            if key in (276, 97):  # Left arrow or 'a'
                self.state = 'albums'
                self.update_view()
            elif key == 273:  # Up arrow
                if self.images:
                    self.image_idx = (self.image_idx - 1) % len(self.images)
                    self.update_view()
            elif key == 274:  # Down arrow
                if self.images:
                    self.image_idx = (self.image_idx + 1) % len(self.images)
                    self.update_view()


class GalleryApp(App):
    def build(self):
        Window.size = (1920, 1080)
        Window.fullscreen = False
        return GalleryBrowser()

if __name__ == '__main__':
    GalleryApp().run()