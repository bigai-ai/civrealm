## Actions


### Unit Actions

<table>
    <tr>
        <td bgcolor="Lavender"><b>Action Class</b></td>
        <td bgcolor="Lavender"><b>Action Description</b></td>
        <td bgcolor="Lavender"><b>Parameter</b></td>
    </tr>
    <tr>
        <td>ActGoto</td>
        <td>Go to a target tile</td>
        <td rowspan="2" style="vertical-align: middle;">the target tile</td>
    </tr>
    <tr>
        <td>ActHutEnter</td>
        <td>Enter a hut in the target tile for random events</td>
    </tr>
    <tr>
        <td>ActEmbark</td>
        <td>Embark on a target boat mooring in an ocean tile</td>
        <td rowspan="2" style="vertical-align: middle;">the target boat unit</td>
    </tr>
    <tr>
        <td>ActDisembark</td>
        <td>Disembark from a target boat mooring in an ocean tile</td>
    </tr>
    <tr>
        <td>ActUnloadUnit</td>
        <td>Unload all units carried by the transporter unit</td>
        <td rowspan="4" style="vertical-align: middle;">-</td>
    </tr>
    <tr>
        <td>ActBoard</td>
        <td>Board a boat mooring in the city of the current tile</td>
    </tr>
    <tr>
        <td>ActDeboard</td>
        <td>Deboard a boat mooring in the city of the current tile</td>
    </tr>
    <tr>
        <td>ActFortify</td>
        <td>Fortify in the current tile</td>
    </tr>
    <tr>
        <td>ActAttack</td>
        <td>Attack the unit in a target tile</td>
        <td>the target tile</td>
    </tr>
    <tr>
        <td>ActSpyBribeUnit</td>
        <td>Bribe a unit of other players to join us</td>
        <td>the target unit</td>
    </tr>
    <tr>
        <td>ActConquerCity</td>
        <td>Conquer a city belongs to other players</td>
        <td rowspan="3" style="vertical-align: middle;">the target city</td>
    </tr>
    <tr>
        <td>ActSpySabotageCity</td>
        <td>Sabotage a city belongs to other players</td>
    </tr>
    <tr>
        <td>ActSpyStealTech</td>
        <td>Steal technology from a city belongs to other players</td>
    </tr>
    <tr>
        <td>ActMine</td>
        <td>Mine in the current tile</td>
        <td rowspan="16" style="vertical-align: middle;">-</td>
    </tr>
    <tr>
        <td>ActIrrigation</td>
        <td>Irrigate in the current tile</td>
    </tr>
    <tr>
        <td>ActBuildRoad</td>
        <td>Build road in the current tile</td>
    </tr>
    <tr>
        <td>ActBuildRailRoad</td>
        <td>Build railroad in the current tile</td>
    </tr>
    <tr>
        <td>ActPlant</td>
        <td>Plant trees in the current tile</td>
    </tr>
    <tr>
        <td>ActBuildCity</td>
        <td>Build a city in the current tile</td>
    </tr>
    <tr>
        <td>ActAirbase</td>
        <td>Build airbase in the current tile</td>
    </tr>
    <tr>
        <td>ActFortress</td>
        <td>Build fortress in the current tile</td>
    </tr>
    <tr>
        <td>ActTransform</td>
        <td>Transform the terrain of the current tile</td>
    </tr>
    <tr>
        <td>ActPillage</td>
        <td>Pillage an infrastructure in the current tile</td>
    </tr>
    <tr>
        <td>ActCultivate</td>
        <td>Cultivate the forest in the current tile into a plain</td>
    </tr>
    <tr>
        <td>ActUpgrade</td>
        <td>Upgrade the unit</td>
    </tr>
    <tr>
        <td>ActDisband</td>
        <td>Disband the unit itself to save cost</td>
    </tr>
    <tr>
        <td>ActKeepActivity</td>
        <td>Keep the current activity in this turn</td>
    </tr>
    <tr>
        <td>ActHomecity</td>
        <td>Set the unit's home city as the city in the current tile</td>
    </tr>
    <tr>
        <td>ActJoinCity</td>
        <td>Join the city in the current tile (increase city population)</td>
    </tr>
    <tr>
        <td>ActMarketplace</td>
        <td>Sell goods in the target city's marketplace</td>
        <td rowspan="4" style="vertical-align: middle;">the target city</td>
    </tr>
    <tr>
        <td>ActInvestigateSpend</td>
        <td>Investigate a target city belongs to other players</td>
    </tr>
    <tr>
        <td>ActEmbassyStay</td>
        <td>Establish embassy in a target city belongs to other players</td>
    </tr>
    <tr>
        <td>ActTradeRoute</td>
        <td>Establish a trade route from the unit's home city to the target city</td>
    </tr>
</table>


### City Actions

<table>
    <tr>
        <td bgcolor="Lavender"><b>Action Class</b></td>
        <td bgcolor="Lavender"><b>Action Description</b></td>
        <td bgcolor="Lavender"><b>Parameter</b></td>
    </tr>
    <tr>
        <td>CityWorkTile</td>
        <td>Choose a working tile for city</td>
        <td rowspan="2" style="vertical-align: middle;">the target tile</td>
    </tr>
    <tr>
        <td>CityUnworkTile</td>
        <td>Do not work on a tile</td>
    </tr>
    <tr>
        <td>CityBuyProduction</td>
        <td>Buy building or unit</td>
        <td>-</td>
    </tr>
    <tr>
        <td>CityChangeSpecialist</td>
        <td>Change the type of a specialist</td>
        <td>type of the target specialist</td>
    </tr>
    <tr>
        <td>CitySellImprovement</td>
        <td>Sell a building</td>
        <td rowspan="2" style="vertical-align: middle;">the target building</td>
    </tr>
    <tr>
        <td>CityChangeImprovementProduction</td>
        <td>Construct a building</td>
    </tr>
    <tr>
        <td>CityChangeUnitProduction</td>
        <td>Produce a unit</td>
        <td>the target unit</td>
    </tr>
</table>


### Diplomacy Actions

<table>
    <tr>
        <td bgcolor="Lavender"><b>Action Class</b></td>
        <td bgcolor="Lavender"><b>Action Description</b></td>
        <td bgcolor="Lavender"><b>Parameter</b></td>
    </tr>
    <tr>
        <td>StartNegotiate</td>
        <td>Start a negotiation</td>
        <td rowspan="5" style="vertical-align: middle;">target player ID</td>
    </tr>
    <tr>
        <td>StopNegotiate</td>
        <td>End a negotiation</td>
    </tr>
    <tr>
        <td>AcceptTreaty</td>
        <td>Accept treaties</td>
    </tr>
    <tr>
        <td>CancelTreaty</td>
        <td>Cancel a treaty</td>
    </tr>
    <tr>
        <td>CancelVision</td>
        <td>Cancel sharing vision</td>
    </tr>
    <tr>
        <td>AddClause</td>
        <td>Add a basic clause</td>
        <td>target player ID + target basic clause type</td>
    </tr>
    <tr>
        <td>AddTradeTechClause</td>
        <td>Add a trading tech clause</td>
        <td>target player ID + giver ID + target technology ID</td>
    </tr>
    <tr>
        <td>AddTradeGoldClause</td>
        <td>Add a trading gold clause</td>
        <td>target player ID + giver ID + how much gold</td>
    </tr>
    <tr>
        <td>AddTradeCityClause</td>
        <td>Add a trading city clause</td>
        <td>target player ID + giver ID + target city ID</td>
    </tr>
    <tr>
        <td>RemoveClause</td>
        <td>Remove a clause</td>
        <td>target player ID + parameters of the target clause</td>
    </tr>
</table>



### Government Actions

<table>
    <tr>
        <td bgcolor="Lavender"><b>Action Class</b></td>
        <td bgcolor="Lavender"><b>Action Description</b></td>
        <td bgcolor="Lavender"><b>Parameter</b></td>
    </tr>
    <tr>
        <td>ChangeGovernment</td>
        <td>Revolution</td>
        <td>the target Government ID</td>
    </tr>
    <tr>
        <td>SetSciLuxTax</td>
        <td>Set rates of tax + science + luxury</td>
        <td>rates of tax + science + luxury</td>
    </tr>
</table>


### Technology Actions

<table>
    <tr>
        <td bgcolor="Lavender"><b>Action Class</b></td>
        <td bgcolor="Lavender"><b>Action Description</b></td>
        <td bgcolor="Lavender"><b>Parameter</b></td>
    </tr>
    <tr>
        <td>ActChooseResearchTech</td>
        <td>Set a current research goal</td>
        <td>the target technology ID</td>
    </tr>
    <tr>
        <td>ActChooseResearchGoal</td>
        <td>Set a future research goal</td>
        <td>the target technology ID</td>
    </tr>
</table>



