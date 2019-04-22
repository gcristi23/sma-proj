class Message:
    REQUEST = 0
    INFORM = 1
    PROPOSE = 2
    DECLINE = 3
    ACCEPT = 4

    def __init__(self, sender, dest, content, msg_type, conv_id):
        self.sender = sender
        self.dest = dest
        self.msg_type = msg_type
        self.content = content
        self.conv_id = conv_id

    def __str__(self):
        msg = "Message from: %s to: %s\n" % (self.sender, self.dest)
        msg += "Content: %s\n" % self.content
        msg += "-====END-MESSAGE====-\n"
        return msg
