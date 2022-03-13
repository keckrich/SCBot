from turtle import pos
from sc2.bot_ai import BotAI  # parent class we inherit from
from sc2.data import Difficulty, Race  # difficulty for bots, race for the 1 of 3 races
from sc2.main import run_game  # function that facilitates actually running the agents in games
from sc2.player import Bot, Computer  #wrapper for whether or not the agent is one of your bots, or a "computer" player
from sc2 import maps  # maps method for loading maps to play in.
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit
from sc2.position import Point2
import random

class IncrediBot(BotAI): # inhereits from BotAI (part of BurnySC2)
    starting_nexus: Unit
    async def on_step(self, iteration: int): # on_step is a method that is called every step of the game.
        # print(
        #     f"{iteration}, n_workers: {self.workers.amount}, n_idle_workers: {self.workers.idle.amount},", \
        #     # f"minerals: {self.minerals}, gas: {self.vespene}, cannons: {self.structures(UnitTypeId.PHOTONCANNON).amount},", \
        #     f"pylons: {self.structures(UnitTypeId.PYLON).amount}, nexus: {self.structures(UnitTypeId.NEXUS).amount}", \
        #     f"gateways: {self.structures(UnitTypeId.GATEWAY).amount}, cybernetics cores: {self.structures(UnitTypeId.CYBERNETICSCORE).idle.amount}", \
        #     # f"stargates: {self.structures(UnitTypeId.STARGATE).amount}, voidrays: {self.units(UnitTypeId.VOIDRAY).amount}, supply: {self.supply_used}/{self.supply_cap}", \
        #     "done")

        last_expanstion: int = 0
        global starting_nexus
        
        def closest_nexus(assimilator: Unit):
            distance = 10000000000
            closest_nexus = None
            for nexus in self.townhalls:
                d = nexus.position - assimilator.position
                d = d*d
        
        def warp_in_zelot():
            for sg in self.structures(UnitTypeId.GATEWAY).ready.idle:
                    if self.can_afford(UnitTypeId.ZEALOT):
                        sg.train(UnitTypeId.ZEALOT)
                

        # begin logic:

        await self.distribute_workers() # put idle workers back to work

        for assimilator in self.gas_buildings: # check if all assimilatoprs have three workers and train more
            if assimilator.surplus_harvesters < 0 and self.supply_workers < 100:
                closest_nexus = assimilator.position.sort_by_distance(self.townhalls)[0]
                if closest_nexus.is_idle and self.can_afford(UnitTypeId.PROBE):
                    closest_nexus.train(UnitTypeId.PROBE)

        # if self.can_afford(UnitTypeId.NEXUS):  # can we afford one?
        #         await self.expand_now()  # build one!

        if iteration < 380 and iteration > 30: # we are in the opener 
            starting_base: Unit = self.townhalls[0] 
            if  self.supply_left < 6: # if we are close to suply cap build a pylon
                if self.can_afford(UnitTypeId.PYLON) and self.already_pending(UnitTypeId.PYLON) + self.structures.filter(lambda structure: structure.type_id == UnitTypeId.PYLON and not structure.is_ready).amount == 0:
                    pos: Point2 = (self.main_base_ramp.protoss_wall_pylon + starting_base.position) / 2
                    await self.build(UnitTypeId.PYLON, near=pos)

            # build a gateway in the wall 
            if self.structures.filter(lambda structure: structure.type_id == UnitTypeId.PYLON and structure.is_ready).amount == 1:
                if self.already_pending(UnitTypeId.GATEWAY) + self.structures.filter(lambda structure: structure.type_id == UnitTypeId.GATEWAY).amount == 0:
                    if self.can_afford(UnitTypeId.GATEWAY):
                        await self.build(UnitTypeId.GATEWAY, near=self.main_base_ramp.protoss_wall_buildings[0])

            # build a cybernetics core in the wall 
            if self.structures.filter(lambda structure: structure.type_id == UnitTypeId.GATEWAY and structure.is_ready).amount == 1:
                if self.already_pending(UnitTypeId.CYBERNETICSCORE) + self.structures.filter(lambda structure: structure.type_id == UnitTypeId.CYBERNETICSCORE).amount == 0:
                    if self.can_afford(UnitTypeId.CYBERNETICSCORE):
                        await self.build(UnitTypeId.CYBERNETICSCORE, near=self.main_base_ramp.protoss_wall_buildings[1])
                if self.units(UnitTypeId.ZEALOT).amount  == 0:
                    warp_in_zelot()

            # check if more probes are needed
            if starting_base.surplus_harvesters < 0: 
                if starting_base.is_idle and self.can_afford(UnitTypeId.PROBE):
                    starting_base.train(UnitTypeId.PROBE)

            # move zealot to wall 
            if self.units(UnitTypeId.ZEALOT).amount > 0:
                if self.units(UnitTypeId.ZEALOT)[0] != self.main_base_ramp.protoss_wall_warpin:
                    self.units(UnitTypeId.ZEALOT)[0].move(self.main_base_ramp.protoss_wall_warpin)
                else:
                     self.units(UnitTypeId.ZEALOT)[0].hold

            if iteration > 75:
                vespenes = self.vespene_geyser.closer_than(15, starting_base)
                for vespene in vespenes:
                    if self.can_afford(UnitTypeId.ASSIMILATOR) and self.already_pending(UnitTypeId.ASSIMILATOR) + self.structures.filter(lambda structure: structure.type_id == UnitTypeId.ASSIMILATOR and not structure.is_ready).amount == 0:
                        await self.build(UnitTypeId.ASSIMILATOR, vespene)

        elif iteration < 30: # build wall pylon
            if self.can_afford(UnitTypeId.PYLON) and self.already_pending(UnitTypeId.PYLON) + self.structures.filter(lambda structure: structure.type_id == UnitTypeId.PYLON and structure.is_ready).amount == 0:
                await self.build(UnitTypeId.PYLON, near=self.main_base_ramp.protoss_wall_pylon)

        else:
            random_nexus = random.choice(self.townhalls)
            # check if more probes are needed
            if random_nexus.surplus_harvesters < 0 and self.supply_workers < 100: 
                if random_nexus.is_idle and self.can_afford(UnitTypeId.PROBE):
                    random_nexus.train(UnitTypeId.PROBE)

            # build more pylons when needed 
            if  self.supply_left < 6 and self.supply_cap != 200: # if we are close to suply cap build a pylon
                if self.can_afford(UnitTypeId.PYLON) and self.already_pending(UnitTypeId.PYLON) + self.structures.filter(lambda structure: structure.type_id == UnitTypeId.PYLON and not structure.is_ready).amount == 0:
                    pos: Point2 = (self.main_base_ramp.protoss_wall_pylon + starting_nexus.position) / 2
                    await self.build(UnitTypeId.PYLON, near=pos)

            # build assimilators
            vespenes = self.vespene_geyser.closer_than(15, random_nexus)
            for vespene in vespenes:
                if self.can_afford(UnitTypeId.ASSIMILATOR) and self.already_pending(UnitTypeId.ASSIMILATOR) + self.structures.filter(lambda structure: structure.type_id == UnitTypeId.ASSIMILATOR and not structure.is_ready).amount == 0:
                    await self.build(UnitTypeId.ASSIMILATOR, vespene)

            # build a voidray 
            if self.can_afford(UnitTypeId.VOIDRAY):
                for sg in self.structures(UnitTypeId.STARGATE).ready.idle:
                    sg.train(UnitTypeId.VOIDRAY)

            # build a stargate
            if self.structures.filter(lambda structure: structure.type_id == UnitTypeId.CYBERNETICSCORE and structure.is_ready).amount == 1:
                if self.already_pending(UnitTypeId.STARGATE) == 0 and self.structures.filter(lambda structure: structure.type_id == UnitTypeId.STARGATE).amount < 8:
                    if self.can_afford(UnitTypeId.STARGATE):
                        pos: Point2 = (self.main_base_ramp.protoss_wall_pylon + starting_nexus.position) / 2
                        await self.build(UnitTypeId.STARGATE, near=pos)

            # expand 
            if self.minerals > 800 and iteration - last_expanstion > 100:
                last_expanstion = iteration
                await self.expand_now()

            # get upgrades 
            if self.units(UnitTypeId.VOIDRAY).amount > 3:
            
                if self.can_afford(UpgradeId.PROTOSSAIRWEAPONSLEVEL1):
                    self.research(UpgradeId.PROTOSSAIRWEAPONSLEVEL1)
                elif self.can_afford(UpgradeId.PROTOSSAIRARMORSLEVEL1):
                    self.research(UpgradeId.PROTOSSAIRARMORSLEVEL1)
                elif self.can_afford(UpgradeId.PROTOSSAIRWEAPONSLEVEL2):
                    self.research(UpgradeId.PROTOSSAIRWEAPONSLEVEL2)
                elif self.can_afford(UpgradeId.PROTOSSAIRARMORSLEVEL2):
                    self.research(UpgradeId.PROTOSSAIRARMORSLEVEL2)

                # build a forge if there is not one
                if self.already_pending(UnitTypeId.FORGE) + self.structures.filter(lambda structure: structure.type_id == UnitTypeId.FORGE).amount == 0:
                    if self.can_afford(UnitTypeId.FORGE):
                        pos: Point2 = (self.main_base_ramp.protoss_wall_pylon + starting_nexus.position) / 2
                        await self.build(UnitTypeId.FORGE, near=pos)
                else:
                    if self.can_afford(UpgradeId.PROTOSSSHIELDSLEVEL1):
                        self.research(UpgradeId.PROTOSSSHIELDSLEVEL1)

                # build a fleet beacon if there is not one and get voidray speed
                if self.already_pending(UnitTypeId.FLEETBEACON) + self.structures.filter(lambda structure: structure.type_id == UnitTypeId.FLEETBEACON).amount == 0:
                    if self.can_afford(UnitTypeId.FLEETBEACON):
                        pos: Point2 = (self.main_base_ramp.protoss_wall_pylon + starting_nexus.position) / 2
                        await self.build(UnitTypeId.FLEETBEACON, near=pos)
                else:
                    if self.can_afford(UpgradeId.VOIDRAYSPEEDUPGRADE):
                        self.research(UpgradeId.VOIDRAYSPEEDUPGRADE)

            # get observer
            if self.units(UnitTypeId.VOIDRAY).amount > 3:
                if self.already_pending(UnitTypeId.ROBOTICSFACILITY) + self.structures.filter(lambda structure: structure.type_id == UnitTypeId.ROBOTICSFACILITY).amount == 0:
                    if self.can_afford(UnitTypeId.ROBOTICSFACILITY):
                        pos: Point2 = (self.main_base_ramp.protoss_wall_pylon + starting_nexus.position) / 2
                        await self.build(UnitTypeId.ROBOTICSFACILITY, near=pos)
                elif self.structures(UnitTypeId.ROBOTICSFACILITY).ready.idle.amount > 0:
                    if self.units(UnitTypeId.OBSERVER).amount < 1 and self.can_afford(UnitTypeId.OBSERVER):
                        self.structures(UnitTypeId.ROBOTICSFACILITY).ready.idle[0].train(UnitTypeId.OBSERVER)
            if self.units(UnitTypeId.OBSERVER).idle.amount > 0:
                for obv in self.units(UnitTypeId.OBSERVER).idle:
                    obv.move(self.units(UnitTypeId.VOIDRAY).random)

            if self.supply_used > 190:
                if self.enemy_units:
                    for vr in self.units(UnitTypeId.VOIDRAY).idle:
                        vr.attack(random.choice(self.enemy_units))
                elif self.enemy_structures:
                    for vr in self.units(UnitTypeId.VOIDRAY):
                        vr.attack(random.choice(self.enemy_structures))
            elif self.units(UnitTypeId.VOIDRAY).amount > 6:
                for vr in self.units(UnitTypeId.VOIDRAY):
                    pos: Point2 = (self.main_base_ramp.protoss_wall_pylon + self.game_info.map_center) / 2
                    vr.attack(pos)
            else:
                 for vr in self.units(UnitTypeId.VOIDRAY).idle:
                    pos: Point2 = (self.main_base_ramp.protoss_wall_pylon + self.game_info.map_center) / 2
                    vr.attack(pos)


        # if iteration == 500: # we are in the opener 
        #     x = 1

        # if we have more than 3 voidrays, let's attack!
        # if self.units(UnitTypeId.VOIDRAY).amount >= 3:
        #     if self.enemy_units:
        #         for vr in self.units(UnitTypeId.VOIDRAY).idle:
        #             vr.attack(random.choice(self.enemy_units))
            
        #     elif self.enemy_structures:
        #         for vr in self.units(UnitTypeId.VOIDRAY).idle:
        #             vr.attack(random.choice(self.enemy_structures))

        #     # otherwise attack enemy starting position
        #     else:
        #         for vr in self.units(UnitTypeId.VOIDRAY).idle:
        #             vr.attack(self.enemy_start_locations[0])

    async def on_start(self):
        print("starting")
        global starting_nexus
        starting_nexus = self.townhalls[0]


run_game(  # run_game is a function that runs the game.
    maps.get("2000AtmospheresAIE"), # the map we are playing on
    [Bot(Race.Protoss, IncrediBot()), # runs our coded bot, protoss race, and we pass our bot object 
     Computer(Race.Terran, Difficulty.Harder)], # runs a pre-made computer agent, zerg race, with a hard difficulty.
    realtime=False, # When set to True, the agent is limited in how long each step can take to process.
    disable_fog=True,
)