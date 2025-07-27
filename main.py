import os, sys, random
from io import BytesIO

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.graphics.texture import Texture

from PIL import Image as PILImage, ImageDraw, ImageFont

# Rutas y datos
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

IMG_FOLDER = os.path.join(BASE_PATH, "img")

STAGE_NAMES = [
    "Battlefield", "Small Battlefield", "Final Destination",
    "Yoshi's Story", "Pokemon Stadium 2", "Smashville",
    "Kalos Pokemon League", "Town and City", "Hollow Bastion"
]

STAGE_FILES = [
    "battlefield.png", "small_battlefield.png", "final_destination.png",
    "yoshis_story.png", "pokemon_stadium_2.png", "smashville.png",
    "kalos_pokemon_league.png", "town_and_city.png", "hollow_bastion.png"
]

# Jugadores iniciales
PLAYERS = ["Zaichu", "Kivirius", "Cabrerasaurio", "Khancerius"]

# Tamaños de texto en PIL (se usa fuente por defecto en Android)
FONT_SIZE_PLAYER = 20
FONT_SIZE_STAGE = 24
FONT_SIZE_PICKED_PLAYER = 28


def pil_to_texture(pil_image):
    """Convierte un PIL RGBA a Texture de Kivy."""
    pil = pil_image.convert("RGBA")
    width, height = pil.size
    data = pil.tobytes()
    tex = Texture.create(size=(width, height), colorfmt='rgba')
    tex.blit_buffer(data, bufferfmt='ubyte', colorfmt='rgba')
    tex.flip_vertical()
    return tex


class StageSelectorKivy(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=10, padding=10, **kwargs)
        self.banned_stages = {}
        self.selected_stage = None
        self.current_turn = None
        self.mode = None       # "set" o "match"
        self.pick_mode = False

        # Top bar: spinners y botones
        top = BoxLayout(size_hint_y=None, height='40dp', spacing=8)
        self.sp1 = Spinner(text="Jugador 1", values=PLAYERS, size_hint_x=None, width='120dp')
        self.sp2 = Spinner(text="Jugador 2", values=PLAYERS, size_hint_x=None, width='120dp')
        top.add_widget(self.sp1)
        top.add_widget(self.sp2)
        top.add_widget(Button(text="Start Set", on_press=lambda *_: self.start_set()))
        top.add_widget(Button(text="Match",    on_press=lambda *_: self.start_match()))
        top.add_widget(Button(text="Reset",    on_press=lambda *_: self.reset_stage_images()))
        top.add_widget(Button(text="Agregar jugador", on_press=lambda *_: self.agregar_jugador()))
        top.add_widget(Button(text="Eliminar jugador", on_press=lambda *_: self.eliminar_jugador()))
        self.add_widget(top)

        # Etiqueta de info
        self.info_label = Label(text="", size_hint_y=None, height='30dp', font_size='16sp')
        self.add_widget(self.info_label)

        # Grid de escenarios
        self.stage_grid = GridLayout(cols=3, spacing=8)
        self.add_widget(self.stage_grid)

        # Carga inicial de imágenes PIL + Kivy Image
        self.stage_images_pil = []
        self.stage_widgets = []
        self.load_stage_images()

    def load_stage_images(self):
        for idx, fname in enumerate(STAGE_FILES):
            path = os.path.join(IMG_FOLDER, fname)
            pil_img = PILImage.open(path).resize((240, 135))
            self.stage_images_pil.append(pil_img)

            tex = pil_to_texture(pil_img)
            img_w = Image(texture=tex, size_hint=(None, None), size=(240, 135))
            img_w.idx = idx
            img_w.allow_stretch = True
            img_w.keep_ratio = True
            img_w.bind(on_touch_down=self.on_stage_touch)

            self.stage_widgets.append(img_w)
            self.stage_grid.add_widget(img_w)

        # Dibuja solo footer en todos
        self.reset_stage_images()

    def on_stage_touch(self, widget, touch):
        if widget.collide_point(*touch.pos):
            self.on_stage_click(widget.idx)
        return False

    def on_stage_click(self, idx):
        name = STAGE_NAMES[idx]
        if not self.mode or name in self.banned_stages or self.selected_stage:
            return

        if self.mode == "set":
            self.ban_stage(idx)
        else:  # match
            if not self.pick_mode:
                self.ban_stage(idx)
            else:
                self.pick_stage(idx)

        # Animación simple de borde: resalta por 0.1s
        w = self.stage_widgets[idx]
        original_color = w.color
        w.color = (0.5,0.5,0.5,1)
        Clock.schedule_once(lambda dt: setattr(w, 'color', original_color), 0.1)

    def ban_stage(self, idx):
        name = STAGE_NAMES[idx]
        self.banned_stages[name] = self.current_turn
        self.update_stage_image(idx, banned=True)

        if self.mode == "set":
            if len(self.banned_stages) == 8:
                # pick automático último
                rem = [s for s in STAGE_NAMES if s not in self.banned_stages][0]
                i = STAGE_NAMES.index(rem)
                self.selected_stage = rem
                self.update_stage_image(i, picked=True)
                self.info_label.text = f"{self.current_turn} eligió {rem}"
                self.mode = None
            else:
                self.switch_turn()
                self.info_label.text = f"{self.current_turn} banea"
        else:
            cnt = len(self.banned_stages)
            if cnt < 3:
                self.info_label.text = f"{self.current_turn} banea ({cnt}/3)"
            else:
                self.pick_mode = True
                loser = (self.sp2.text if self.current_turn == self.sp1.text else self.sp1.text)
                self.current_turn = loser
                self.info_label.text = f"{loser} elige escenario"

    def pick_stage(self, idx):
        stage = STAGE_NAMES[idx]
        self.selected_stage = stage
        self.update_stage_image(idx, picked=True)
        self.info_label.text = f"{self.current_turn} eligió {stage}"
        self.mode = None
        self.pick_mode = False

    def switch_turn(self):
        p1, p2 = self.sp1.text, self.sp2.text
        self.current_turn = p2 if self.current_turn == p1 else p1

    def update_stage_image(self, idx, banned=False, picked=False):
        base = self.stage_images_pil[idx].copy().convert("RGBA")
        draw = ImageDraw.Draw(base)

        # Carga fuente genérica de PIL (por defecto)
        try:
            f_p = ImageFont.load_default()
            f_s = ImageFont.load_default()
            f_b = ImageFont.load_default()
        except:
            f_p = f_s = f_b = ImageFont.load_default()

        # Overlay y texto central
        if banned:
            overlay = PILImage.new("RGBA", base.size, (255, 0, 0, 120))
            base = PILImage.alpha_composite(base, overlay)
            draw.line((0, 0, base.width, base.height), fill=(255, 0, 0, 200), width=10)
            draw.line((base.width, 0, 0, base.height), fill=(255, 0, 0, 200), width=10)
            ply = self.banned_stages.get(STAGE_NAMES[idx], "")
            if ply:
                self._draw_text_border(draw, base, f"Baneado por {ply}", f_p)
        elif picked:
            overlay = PILImage.new("RGBA", base.size, (0, 255, 0, 120))
            base = PILImage.alpha_composite(base, overlay)
            self._draw_text_border(draw, base, "¡Elegido!", f_b)

        # Footer con nombre de stage
        self._draw_footer(draw, base, STAGE_NAMES[idx], f_s)

        # Actualiza textura Kivy
        tex = pil_to_texture(base)
        w = self.stage_widgets[idx]
        w.texture = tex

    def _draw_text_border(self, draw, img, text, font):
        x, y = img.width//2, img.height//2
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                if dx or dy:
                    draw.text((x+dx, y+dy), text, font=font, fill="black", anchor="mm")
        draw.text((x, y), text, font=font, fill="white", anchor="mm")

    def _draw_footer(self, draw, img, text, font):
        footer_h = 20
        draw.rectangle([0, img.height-footer_h, img.width, img.height], fill=(0, 0, 0, 180))
        x, y = img.width//2, img.height-footer_h//2
        # borde y texto
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                draw.text((x+dx, y+dy), text, font=font, fill="black", anchor="mm")
        draw.text((x, y), text, font=font, fill="white", anchor="mm")

    def start_set(self):
        if (self.sp1.text == self.sp2.text) or not self.sp1.text or not self.sp2.text:
            self._alert("Error", "Elegí dos jugadores distintos")
            return
        self.banned_stages.clear()
        self.selected_stage = None
        self.mode = "set"
        self.current_turn = random.choice([self.sp1.text, self.sp2.text])
        self.info_label.text = f"{self.current_turn} banea"
        self.reset_stage_images()

    def start_match(self):
        if (self.sp1.text == self.sp2.text) or not self.sp1.text or not self.sp2.text:
            self._alert("Error", "Elegí dos jugadores distintos")
            return
        self.banned_stages.clear()
        self.selected_stage = None
        self.mode = "match"
        self.pick_mode = False
        self.reset_stage_images()
        self.choose_winner_popup()

    def reset_stage_images(self):
        # Redibuja solo footers
        for idx in range(len(self.stage_images_pil)):
            self.update_stage_image(idx)

    # Popups

    def _alert(self, title, msg):
        pop = Popup(title=title,
                    content=Label(text=msg),
                    size_hint=(.6, .4))
        pop.open()

    def agregar_jugador(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        inp = Label(text="Ingresa nombre del nuevo jugador")
        ti = Label(text_input="")  # simplificación: no input real
        inp2 = Label(text="(implementa TextInput aquí si lo deseas)")
        btn = Button(text="Cerrar", size_hint_y=None, height='40dp',
                     on_press=lambda *_: popup.dismiss())
        content.add_widget(inp)
        content.add_widget(inp2)
        content.add_widget(btn)
        popup = Popup(title="Agregar jugador", content=content,
                      size_hint=(.8, .5))
        popup.open()

    def eliminar_jugador(self):
        if not PLAYERS:
            self._alert("Sin jugadores", "No hay jugadores para eliminar.")
            return
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        sp = Spinner(text="Selecciona jugador", values=PLAYERS)
        btn = Button(text="Eliminar", size_hint_y=None, height='40dp',
                     on_press=lambda *_: self._do_eliminar(sp.text, popup))
        content.add_widget(sp)
        content.add_widget(btn)
        popup = Popup(title="Eliminar jugador", content=content,
                      size_hint=(.8, .5))
        popup.open()

    def _do_eliminar(self, nombre, popup):
        if nombre in PLAYERS:
            PLAYERS.remove(nombre)
            self.sp1.values = PLAYERS
            self.sp2.values = PLAYERS
        popup.dismiss()

    def choose_winner_popup(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text="¿Quién gana la ronda?"))
        for p in (self.sp1.text, self.sp2.text):
            content.add_widget(Button(text=p,
                                      on_press=lambda btn, pl=p: self._set_winner(pl, popup)))
        popup = Popup(title="Elegí ganador", content=content,
                      size_hint=(.8, .6))
        popup.open()

    def _set_winner(self, pl, popup):
        self.current_turn = pl
        self.info_label.text = f"{pl} banea"
        popup.dismiss()


class StageSelectorApp(App):
    def build(self):
        return StageSelectorKivy()


if __name__ == "__main__":
    StageSelectorApp().run()
