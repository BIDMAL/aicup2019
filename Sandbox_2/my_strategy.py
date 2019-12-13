import model


class Calc:
    @staticmethod
    def distance_sqr(a, b):
        return (a.x - b.x) ** 2 + (a.y - b.y) ** 2

    @staticmethod
    def sign(a):
        result = None
        if a > 0:
            result = 1
        elif a < 0:
            result = -1
        else:
            result = 0
        return result


class MyStrategy:
    def __init__(self):
        self.prev_enemy_pos = None
        self.enemy_velocity = model.Vec2Double(0, 0)
        self.expected_enemy_pos = None

    def calc_objects(self, unit, game):
        nearest_enemy = min(
            filter(lambda u: u.player_id != unit.player_id, game.units),
            key=lambda u: Calc.distance_sqr(u.position, unit.position),
            default=None)

        nearest_weapon = min(
            filter(lambda box: isinstance(
                box.item, model.Item.Weapon), game.loot_boxes),
            key=lambda box: Calc.distance_sqr(box.position, unit.position),
            default=None)

        nearest_hpbox = min(
            filter(lambda box: isinstance(
                box.item, model.Item.HealthPack), game.loot_boxes),
            key=lambda box: Calc.distance_sqr(box.position, unit.position),
            default=None)

        expected_enemy_pos = nearest_enemy
        if (self.prev_enemy_pos is not None) and (nearest_enemy is not None):
            self.enemy_velocity = model.Vec2Double(
                nearest_enemy.position.x - self.prev_enemy_pos.x,
                nearest_enemy.position.y - self.prev_enemy_pos.y)
            expected_enemy_pos = model.Vec2Double(
                nearest_enemy.position.x + self.enemy_velocity.x,
                nearest_enemy.position.y + self.enemy_velocity.y)

        return nearest_enemy, nearest_weapon, nearest_hpbox, expected_enemy_pos

    def calc_move(self, unit, nearest_weapon, nearest_enemy, nearest_hpbox):
        target_pos = unit.position
        if unit.weapon is None and nearest_weapon is not None:
            target_pos = nearest_weapon.position
        elif nearest_enemy is not None:
            target_pos = model.Vec2Double(
                nearest_enemy.position.x - 10,
                nearest_enemy.position.y)
        return target_pos

    def calc_aim(self, nearest_enemy, unit, game, debug):
        aim = model.Vec2Double(0, 0)
        shoot = False
        if nearest_enemy is not None:
            shoot = True
            traj_len_x = nearest_enemy.position.x - unit.position.x
            traj_len_y = nearest_enemy.position.y - unit.position.y
            aim = model.Vec2Double(traj_len_x, traj_len_y)

            #sign_x = Calc.sign(traj_len_x)
            #sign_y = Calc.sign(traj_len_y)
            #curr_pos = model.Vec2Double(unit.position.x, unit.position.y)
            #leng = 0
            #poslist = []
            # while Calc.distance_sqr(curr_pos, nearest_enemy.position) >= 1 and leng < 100:
            #    pos_dx = model.Vec2Double(curr_pos.x + sign_x, curr_pos.y)
            #    pos_dy = model.Vec2Double(curr_pos.x, curr_pos.y + sign_y)
            #    if Calc.distance_sqr(pos_dx, nearest_enemy.position) >= Calc.distance_sqr(pos_dy, nearest_enemy.position):
            #        curr_pos.x += sign_x
            #    else:
            #        curr_pos.y += sign_y
#
            #    # debug.draw(model.CustomData.Rect(
            #    #     curr_pos, curr_pos, model.ColorFloat(255, 0, 0, 1)))
            #    poslist.append((curr_pos.x, curr_pos.y))
            #    if game.level.tiles[int(curr_pos.x)][int(curr_pos.y)] == model.Tile.WALL:
            #        shoot = False
            #        break
            #    leng += 1

        return aim, shoot, leng, poslist

    def calc_jump(self):
        jump = True
        # if target_pos.x > unit.position.x and game.level.tiles[int(unit.position.x + 1)][int(unit.position.y)] == model.Tile.WALL:
        #     jump = True
        # if target_pos.x < unit.position.x and game.level.tiles[int(unit.position.x - 1)][int(unit.position.y)] == model.Tile.WALL:
        #     jump = True
        return jump

    def get_action(self, unit, game, debug):
        nearest_enemy, nearest_weapon, nearest_hpbox, expected_enemy_pos = self.calc_objects(
            unit, game)

        target_pos = self.calc_move(
            unit, nearest_weapon, nearest_enemy, nearest_hpbox)
        aim, shoot, leng, poslist = self.calc_aim(
            nearest_enemy, unit, game, debug)

        jump = self.calc_jump()

        #  Debug----------------------
        #debug.draw(model.CustomData.Log("Target pos: {}".format(target_pos)))
        # debug.draw(model.CustomData.Log(
        #    "Expected enemy pos: {}".format(expected_enemy_pos)))
        # debug.draw(model.CustomData.Log(
        #    "Velocity: {}".format(target_pos.x - unit.position.x)))
        #debug.draw(model.CustomData.Log("Jump: {}".format(jump)))
        debug.draw(model.CustomData.Log("Dist X: {}".format(
            nearest_enemy.position.x - unit.position.x)))
        debug.draw(model.CustomData.Log("Dist Y: {}".format(
            nearest_enemy.position.y - unit.position.y)))
        debug.draw(model.CustomData.Log("Trajectory length: {}".format(leng)))
        debug.draw(model.CustomData.Log(
            "poslist: {}".format(poslist)))
        #  /Debug----------------------

        self.prev_enemy_pos = nearest_enemy.position

        return model.UnitAction(
            velocity=(target_pos.x - unit.position.x)*10,
            jump=jump,
            jump_down=not jump,
            aim=aim,
            shoot=shoot,
            reload=False,
            swap_weapon=False,
            plant_mine=False)
