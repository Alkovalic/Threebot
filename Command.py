# This is the template for any command you want Threebot to use.

class Command():

    # info() should return information about the command in some way, shape, or form.
    # Technically, info() isn't required, but it's useful for help commands and such.
    
    def info(self):
        return None

    # run() does what the command wants to do, which is hopefully what YOU want it to do!
    # On the other hand, run is very necessary, as a command without a run method is useless.
    # Always remember to use the  async await  syntax, or the command will never be put into the loop..

    async def run(self, client, message):
        raise NotImplementedError("Method <run> not implemented!")
