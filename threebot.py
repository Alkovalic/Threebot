import discord
import random

from discord.ext import commands
from discord.ext.commands.context import Context

threebot = commands.Bot(command_prefix='~')

@threebot.event
async def on_ready():
    print(f'{threebot.user} online.')

@threebot.command()
async def ping(ctx: Context):
    return await ctx.send('pong')

@threebot.command()
async def santa(ctx: Context, *members: discord.Member):
    if threebot.user in members:
        return await ctx.send("I can't afford presents.")
    
    user_check_failed = False
    for user in members:
        if user.bot:
            user_check_failed = True
            await ctx.send(f"{user.display_name} is a bot, and can't afford presents.")
    if user_check_failed:
        return

    santa_assignments: dict[discord.Member, discord.Member] = generate_santa_assignments(members)
    if not santa_assignments:
        return await ctx.send("Secret Santa requires at least two people.")
    for santa in santa_assignments:
        threebot.loop.create_task(send_santa_assignment(ctx, santa, santa_assignments[santa]))

@santa.error
async def santa_error(ctx: Context, error):
    if isinstance(error, commands.MemberNotFound):
        return await ctx.send(f'The user {error.argument} could not be found. You may need to wrap their name in quotes, or use mentions.')
    print(error)

def generate_santa_assignments(members: tuple[discord.Member]):
    if len(members) < 2:
        return dict()
    
    assignments = dict()
    for member in members:
        other_members = [om for om in members if not om is member]
        random.shuffle(other_members)
        assignments[member] = other_members[0]
    
    return assignments
    
async def send_santa_assignment(ctx, santa, target):
    msg = await santa.send(f"You're the secret Santa for {target.mention}! React to this message to confirm.")
    await threebot.wait_for('raw_reaction_add', check=lambda reaction: reaction.message_id == msg.id)
    await ctx.send(f'{santa.display_name} has confirmed their assignment.')