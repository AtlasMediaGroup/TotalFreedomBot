import discord
import aiofiles
import re

from datetime import datetime
from discord.ext import commands
from checks import *
from functions import *

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
   
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.reaction_roles = []
        
        for file in ['reactionroles.txt']:
            async with aiofiles.open(file, mode='a') as temp:
                pass
        async with aiofiles.open('reactionroles.txt', mode='r') as file:
            lines = await file.readlines()
            for line in lines:
                data = line.split(' ')
                self.bot.reaction_roles.append((int(data[0]), int(data[1]), data[2].strip('\n')))
        
        print(f'[{datetime.utcnow().replace(microsecond=0)} INFO]: [Client] {self.bot.user.name} is online.')
        game = discord.Game('play.totalfreedom.me')
        await self.bot.change_presence(status=discord.Status.online, activity=game)
    
        guildCount = len(self.bot.guilds)
        print(f'[{datetime.utcnow().replace(microsecond=0)} INFO]: [Guilds] self.bot currently in {guildCount} guilds.')
        for guild in self.bot.guilds:
            print(f'[{datetime.utcnow().replace(microsecond=0)} INFO]: [Guilds] Connected to guild: {guild.name}, Owner: {guild.owner}')
        global starttime
        starttime = datetime.utcnow()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild and message.author is message.guild.me and message.channel.id == reports_channel_id:
            await message.add_reaction(clipboard)
        if message.type == discord.MessageType.new_member:
            if re.search('discord\.gg\/[a-zA-z0-9\-]{1,16}', message.author.name.lower()) or re.search('discordapp\.com\/invite\/[a-z0-9]+/ig', message.author.name.lower()):
                await message.author.ban(reason="Name is an invite link.")
                await message.delete()
        bypass_roles = [discord_admin, discord_mod]
        bypass = False
        for role in message.author.roles:
            if role.id in bypass_roles:
                bypass = True
        if not bypass:
            if re.search('discord\.gg\/[a-zA-z0-9\-]{1,16}', message.content) or re.search('discordapp\.com\/invite\/[a-z0-9]+/ig', message.content):
                await message.delete()
                await message.channel.send(f"{message.author.mention} do not post invite links to other discord servers.")
                return
        await self.bot.process_commands(message)
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not isinstance(before.author, discord.Member):
            return
        if before.guild.id != guild_id\
                :
            return
        users = removed_user_mentions(before.mentions, after.mentions)
        roles = removed_role_mentions(before.role_mentions, after.role_mentions)
        if users:
            users = ", ".join([str(member) for member in users])
        if roles:
            roles = ", ".join([role.name for role in roles])
        if not users and not roles:
            return
        embed = discord.Embed(description="In {}".format(before.channel.mention))
        if users:
            embed.add_field(name="Users", value=users, inline=True)
        if roles:
            embed.add_field(name="Roles", value=roles, inline=True)
        embed.color = 0xFF0000
        embed.title = "Message Edit"
        embed.set_footer(text=str(before.author), icon_url=get_avatar(before.author))
        channel = before.guild.get_channel(mentions_channel_id)
        await channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not isinstance(message.author, discord.Member):
            return
        if message.guild.id != guild_id:
            return
        users = None
        roles = None
        if did_mention_other_user(message.mentions, message.author):
            users = ", ".join([str(member) for member in message.mentions])
        if message.role_mentions:
            roles = ", ".join([role.name for role in message.role_mentions])
        if not users and not roles:
            return
        embed = discord.Embed(description="In {}".format(message.channel.mention))
        if users is not None:
            embed.add_field(name="Users", value=users, inline=True)
        if roles is not None:
            embed.add_field(name="Roles", value=roles, inline=True)
        embed.color = 0xFF0000
        embed.title = "Message Deletion"
        embed.set_footer(text=str(message.author), icon_url=get_avatar(message.author))
        channel = message.guild.get_channel(mentions_channel_id)
        await channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await ctx.send('''```py
    {}```'''.format(error))
        print(f'[{datetime.utcnow().replace(microsecond=0)} INFO]: [Commands] {ctx.author} failed running: {ctx.message.content} in guild: {ctx.guild.name}')
    
    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        print(f'[{datetime.utcnow().replace(microsecond=0)} INFO]: [Commands] {ctx.author} ran: {ctx.message.content} in guild: {ctx.guild.name}')
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member == self.bot.user:
            pass
        else:
            for role_id, msg_id, emoji in self.bot.reaction_roles:
                if msg_id == payload.message_id and emoji == str(payload.emoji.name.encode('utf-8')):
                    await payload.member.add_roles(self.bot.get_guild(payload.guild_id).get_role(role_id), reason='reaction')
            if payload.channel_id == reports_channel_id:
                guild = self.bot.get_guild(guild_id)
                reports_channel = self.bot.get_channel(reports_channel_id)
                report = await reports_channel.fetch_message(payload.message_id)
                if report.author == guild.me:
                    if payload.emoji.name == clipboard:
                        await report.add_reaction(confirm)
                        await report.add_reaction(cancel)
                    elif payload.emoji.name == cancel:
                        await report.clear_reactions()
                        await report.add_reaction(clipboard)
                    elif payload.emoji.name == confirm:
                        embed = report.embeds[0]
                        archived_reports_channel = self.bot.get_channel(archived_reports_channel_id)
                        await report.delete()
                        await archived_reports_channel.send("Handled by " + guild.get_member(payload.user_id).mention, embed=embed)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.member == self.bot.user:
            pass
        else:
            for role_id, msg_id, emoji in self.bot.reaction_roles:
                if msg_id == payload.message_id and emoji == str(payload.emoji.name.encode('utf-8')):
                    await self.bot.get_guild(payload.guild_id).get_member(payload.user_id).remove_roles(self.bot.get_guild(payload.guild_id).get_role(role_id), reason='reaction')
                    
def setup(bot):
    bot.add_cog(Events(bot))