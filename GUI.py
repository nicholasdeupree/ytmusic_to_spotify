import tkinter as tk

class GUI:
    def __init__(self, root, setup_ytmusic, setup_spotify, ensure_ytmusic_auth, convert):
        self.root = root
        self.root.title('Music Converter')
        self.root.geometry('500x500')
        self.ytmusic = None
        self.spotify = None
        self.media_type = ''
        self.thumbnails = []
        self.checkbutton_vars = []
        self.convert = convert

        self.setup_ytmusic = setup_ytmusic
        self.setup_spotify = setup_spotify
        self.ensure_ytmusic_auth = ensure_ytmusic_auth

        self.create_source_destination_frame()
        self.create_type_frame()
        self.create_convert_frame()
        self.create_convert_button()

    def create_source_destination_frame(self):
        """Create the frame for source and destination selection."""
        self.snDframe = tk.Frame(self.root, width=450)
        self.snDframe.pack(fill=tk.X)

        self.source_label = tk.Label(master=self.snDframe, text='Source:')
        self.source_label.pack(side=tk.LEFT)

        self.source = tk.StringVar()
        self.source.set('Select Source')
        self.source.trace_add('write', self.check_selection)
        self.source_menu = tk.OptionMenu(self.snDframe, self.source, 'Youtube Music', 'Spotify')
        self.source_menu.pack(side=tk.LEFT)

        self.destination = tk.StringVar()
        self.destination.set('Select Destination')
        self.destination.trace_add('write', self.check_selection)
        self.destination_menu = tk.OptionMenu(self.snDframe, self.destination, 'Youtube Music', 'Spotify')
        self.destination_menu.pack(side=tk.RIGHT)

        self.destination_label = tk.Label(master=self.snDframe, text='Destination:')
        self.destination_label.pack(side=tk.RIGHT)

        

    def create_type_frame(self):
        """Create the frame for selecting the type of media to convert."""
        self.typeFrame = tk.Frame(self.root, width=450)
        self.typeFrame.pack(fill=tk.X)

        self.selected_type = tk.IntVar(value=0)

        self.playlist_button = tk.Radiobutton(master=self.typeFrame, text='Playlist', variable=self.selected_type, value=1, command=lambda: self.set_type("playlist"), state=tk.DISABLED)
        self.song_button = tk.Radiobutton(master=self.typeFrame, text='Song', variable=self.selected_type, value=2, command=lambda: self.set_type("song"), state=tk.DISABLED)
        self.album_button = tk.Radiobutton(master=self.typeFrame, text='Album', variable=self.selected_type, value=3, command=lambda: self.set_type("album"), state=tk.DISABLED)
        self.artist_button = tk.Radiobutton(master=self.typeFrame, text='Artist', variable=self.selected_type, value=4, command=lambda: self.set_type("artist"), state=tk.DISABLED)

        self.playlist_button.pack(side=tk.LEFT, anchor=tk.CENTER)
        self.song_button.pack(side=tk.LEFT, anchor=tk.CENTER)
        self.album_button.pack(side=tk.LEFT, anchor=tk.CENTER)
        self.artist_button.pack(side=tk.LEFT, anchor=tk.CENTER)

    def create_convert_frame(self):
        """Create the frame for displaying items to convert."""
        self.convert_frame = tk.Frame(self.root, width=450, height=400, borderwidth=2, relief='ridge')
        self.convert_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.convert_frame)
        self.scrollbar = tk.Scrollbar(self.convert_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def create_convert_button(self):
        """Create the button to start the conversion process."""
        self.convert_button = tk.Button(self.root, text='Convert', command=self.call_convert, state=tk.DISABLED)
        self.convert_button.pack()

    def call_convert(self):
        ytmusic = self.ytmusic
        spotify = self.spotify
        source = self.source.get()
        destination = self.destination.get()
        media_type = self.media_type
        items = self.checkbutton_vars
        self.convert(ytmusic, spotify, source, destination, media_type, items)    

    def set_type(self, type):
        self.media_type = type
        self.selected_type.set(type)
        self.selected_type_method()

    def check_selection(self, *args):
        if self.source.get() != 'Select Source':
            self.enable_type_buttons()
            if self.destination.get() != 'Select Destination':
                self.convert_button.config(state=tk.NORMAL)
        else:
            self.disable_type_buttons()
        if self.source.get() == 'Youtube Music' or self.destination.get() == 'Youtube Music':
            if not self.ytmusic:
                self.ytmusic = self.setup_ytmusic()
            else:
                self.ytmusic = self.ensure_ytmusic_auth(self.ytmusic) 
        if self.source.get() == "Spotify" or self.destination.get() == "Spotify":
            if not self.spotify:
                self.spotify = self.setup_spotify('user-library-modify, user-library-read, user-follow-read, playlist-modify-public, playlist-modify-private, user-follow-modify')

    def enable_type_buttons(self):
        """Enable the type selection buttons."""
        self.playlist_button.config(state=tk.NORMAL)
        self.song_button.config(state=tk.NORMAL)
        self.album_button.config(state=tk.NORMAL)
        self.artist_button.config(state=tk.NORMAL)

    def disable_type_buttons(self):
        """Disable the type selection buttons."""
        self.playlist_button.config(state=tk.DISABLED)
        self.song_button.config(state=tk.DISABLED)
        self.album_button.config(state=tk.DISABLED)
        self.artist_button.config(state=tk.DISABLED)

    def clear_convert_frame(self):
        """Clear all items from the convert frame."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.checkbutton_vars = []

    def selected_type_method(self, *args):
        self.clear_convert_frame()
        if self.source.get() == 'Youtube Music' and self.ytmusic:
            self.populate_items(self.ytmusic, self.media_type)
        elif self.source.get() == 'Spotify' and self.spotify:
            self.populate_items(self.spotify, self.media_type)

    def populate_items(self, service, media_type):
        """Populate the convert frame with items based on the selected media type."""
        if media_type == 'playlist':
            items = service.get_library_playlists(limit=50000) if service == self.ytmusic else service.current_user_playlists()['items']
        elif media_type == 'album':
            items = service.get_library_albums(limit=50000) if service == self.ytmusic else service.current_user_saved_albums()['items']
        elif media_type == 'artist':
            items = service.get_library_artists(limit=50000) if service == self.ytmusic else service.current_user_followed_artists()['artists']['items']
        elif media_type == 'song':
            items = service.get_library_songs(limit=50000) if service == self.ytmusic else service.current_user_saved_tracks()['items'] #there's a limit. can use offset to try and get more in a looped call

        for item in items:
            #title = item['title'] if service == self.ytmusic else item['name']
            self.add_item_to_convert_frame(item)
            #print(item["track"])

    def add_item_to_convert_frame(self, item):
        """Add an item to the convert frame."""
        item_frame = tk.Frame(self.scrollable_frame)
        item_frame.pack(fill=tk.X, expand=False)

        var = tk.BooleanVar()

        def on_checkbutton_toggle(item_name):
            if var.get():
                self.checkbutton_vars.append(item_name)
            else:
                self.checkbutton_vars.remove(item_name)
            #print(self.checkbutton_vars)
        checkbutton = tk.Checkbutton(item_frame, variable=var, command=lambda: on_checkbutton_toggle(item))
        checkbutton.pack(side=tk.LEFT)
        if self.source.get() == 'Youtube Music':
            if self.media_type == 'artist':
                label = tk.Label(item_frame, text=item['artist'])
            else:
                label = tk.Label(item_frame, text=item['title'])

        else:
            #print(item)
            if self.media_type == 'playlist':
                label = tk.Label(item_frame, text=item['name'])
            elif self.media_type == 'album':
                label = tk.Label(item_frame, text=item['album']['name'])
            elif self.media_type == 'artist':
                label = tk.Label(item_frame, text=item['name'])
            elif self.media_type == 'song':
                label = tk.Label(item_frame, text=item['track']['name'])
        label.pack(side=tk.LEFT)