import discord


async def edit_original_or_followup(inter: discord.Interaction, *args, **kwargs) -> None:
    try:
        await inter.edit_original_response(*args, **kwargs)
    except discord.NotFound:
        await inter.followup.send(*args, **{"ephemeral": True, **kwargs})
