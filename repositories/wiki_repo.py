import discord
from discord.ui import Select, View


class FactsDropdown(Select):
    """Drop down selection for answers."""

    def __init__(self, facts: list, embed: discord.Embed, false_index: int, correction: str) -> None:
        self.embed = embed
        self.false_index = false_index

        options = [discord.SelectOption(label=f"Statement #{i+1}", value=i) for i in range(len(facts))]

        super().__init__(placeholder="Which statement is incorrect?", options=options, min_values=1, max_values=1)

        self.rightEmbed = discord.Embed(
            title="Correct!",
            description=f"Correction: {correction}",
            color=discord.Color.green(),
        )
        self.wrongEmbed = discord.Embed(
            title="Wrong!",
            description=f"The False Statement was #{false_index+1}: {facts[false_index]}\nCorrection: {correction}",
            color=discord.Color.red(),
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Register user's choice and return the answer."""
        self.disabled = True
        embeds = [self.embed]

        if int(self.values[0]) == self.false_index:
            self.rightEmbed.description = f"You selected #{int(self.values[0])+1}"
            embeds.append(self.rightEmbed)
        else:
            embeds.append(self.wrongEmbed)
        await interaction.response.edit_message(view=None, embeds=embeds)


class FactsView(View):
    """Question view with multiple embeds."""

    def __init__(self, *, timeout:float=60, embed:discord.Embed, facts:list, false_index:int, correction:str) -> None:
        super().__init__(timeout=timeout)
        self.add_item(FactsDropdown(embed=embed, facts=facts, false_index=false_index, correction=correction))
