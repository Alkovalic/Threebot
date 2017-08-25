ThreePi takes Threebot arguments, plus a dictionary that contains several directories.
    Class Variables:
        misc_dir is the global miscellaneous directory.
        sound_dir is the global sounds directory.
        server_data_dir is the location of all server data, including local sounds and misc folders.
        server_dict contains all servers' ServerData objects, with the key being the ID of the server.
        creation_time is the time self was instantiated.
        pm_help is the help string used for private message control.
        pm_dict is a dict containing all commands available in PM control.

    load_server_data creates a ServerData object representing the server, and adds it to self.__server_dict.
    If the server has no data in server_data_dir, load_server_data will create directories related to the server.

    init_data calls load_server_data on either a specified server, or all servers
    that self is in.

    get_uptime returns the time passed since self was instantiated.
    Note that get_uptime does NOT return the time since self is actually
    connected to Discord, but the difference is so minuscule that there
    isn't a reason to fix this.

    get_server_data returns the ServerData object associated with the server id of the message object.
    If no message is passed, it returns the dictionary of ServerData itself.

    get_default_sounds and get_default_misc return global directories.

    Returns whether the message's author is able to bypass the whitelist configuration
    of a server.  (True if the author is whitelisted, or if the whitelist is not enabled.)

    init_voice_client handles a server's VoiceClient movement, whether it be the initial creation of the VoiceClient,
    or moving the client to a different channel.
    If the client is "moved" to a channel that doesn't exist, this method does nothing.
    If the author of the message who invoked init_voice_client isn't in a channel, this method does nothing.

    do_default plays sounds and stuff when a message doesn't invoke any commands.

    on_ready initializes all server data when ThreePi boots up by calling init_data.
    Note that this doesn't only call init_data when it starts up, but whenever it reconnects to Discord as well.
    init_data doesn't do anything after the initial boot, as commented in the method itself.

    on_server_join also invokes init_data, but passes the server ThreePi just joined.

    do_pm_command handles private messages sent to ThreePi.  If the author does not have the ability to manage a server,
    ThreePi will do nothing.  Otherwise, it will then execute parse_pm_command.