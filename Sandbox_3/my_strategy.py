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
        self.max_hp = None
        self.curr_hp = None
        self.got_mine = False
        self.swap_weapon = False
        self.rltv_enm_side = None
        self.rltv_enm_dist = 3
        self.shoot_counter = 3

    def calc_objects(self, unit, game):
        if self.max_hp is None:
            self.max_hp = unit.health
        self.curr_hp = unit.health / self.max_hp

        if unit.weapon is not None:
            if unit.weapon.typ == 0:
                self.swap_weapon = True
            else:
                self.swap_weapon = False

        nearest_enemy = min(
            filter(lambda u: u.player_id != unit.player_id, game.units),
            key=lambda u: Calc.distance_sqr(u.position, unit.position),
            default=None)

        if nearest_enemy is not None:
            self.rltv_enm_side = Calc.sign(
                unit.position.x - nearest_enemy.position.x) or - 1
            dist = Calc.distance_sqr(nearest_enemy.position, unit.position)
            if dist < 12:
                self.rltv_enm_dist = 0
            elif dist < 60:
                self.rltv_enm_dist = 1
            elif dist < 300:
                self.rltv_enm_dist = 2
            else:
                self.rltv_enm_dist = 3

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

        nearest_mine = min(
            filter(lambda box: isinstance(
                box.item, model.Item.Mine), game.loot_boxes),
            key=lambda box: Calc.distance_sqr(box.position, unit.position),
            default=None)

        expected_enemy_pos = unit.position
        if (self.prev_enemy_pos is not None) and (nearest_enemy is not None):
            # if unit.weapon is not None:
            #    if unit.weapon.params.bullet.speed == 50:
            #        bullet_coef = 9
            #    else:
            #        bullet_coef = 19
            # else:
            #    bullet_coef = 1
            # debug.draw(model.CustomData.Log(
            #    "bullet_coef: {}".format(bullet_coef)))
            self.enemy_velocity = model.Vec2Double(
                nearest_enemy.position.x - self.prev_enemy_pos.x,
                nearest_enemy.position.y - self.prev_enemy_pos.y)
            expected_enemy_pos = model.Vec2Double(
                nearest_enemy.position.x + self.enemy_velocity.x,
                nearest_enemy.position.y + self.enemy_velocity.y)

        return nearest_enemy, nearest_weapon, nearest_hpbox, nearest_mine, expected_enemy_pos

    def calc_move(self, unit, nearest_weapon, nearest_enemy, nearest_hpbox, nearest_mine):
        target_pos = unit.position
        if (unit.weapon is None and nearest_weapon is not None) or (unit.weapon.typ == 0):
            target_pos = nearest_weapon.position
        elif nearest_hpbox is not None and self.curr_hp <= 0.9:
            target_pos = model.Vec2Double(
                nearest_hpbox.position.x,
                nearest_hpbox.position.y)
        elif nearest_mine is not None:
            target_pos = model.Vec2Double(
                nearest_mine.position.x,
                nearest_mine.position.y)
        elif nearest_enemy is not None:
            target_pos = model.Vec2Double(
                nearest_enemy.position.x + 5 * self.rltv_enm_side,
                nearest_enemy.position.y)
        velocity = (target_pos.x - unit.position.x) * 5
        return target_pos, velocity

    def calc_aim(self, nearest_enemy, unit, game):
        aim = model.Vec2Double(0, 0)
        los = False
        if nearest_enemy is not None:
            los = True
            traj_len_x = nearest_enemy.position.x + \
                self.enemy_velocity.x * 2 - unit.position.x
            traj_len_y = nearest_enemy.position.y + \
                self.enemy_velocity.y * 2 - unit.position.y
            aim = model.Vec2Double(traj_len_x, traj_len_y)

            sign_x = Calc.sign(traj_len_x)
            sign_y = Calc.sign(traj_len_y)
            curr_pos = model.Vec2Double(unit.position.x, unit.position.y)

            while Calc.distance_sqr(curr_pos, nearest_enemy.position) >= 2:
                pos_dx = model.Vec2Double(curr_pos.x + sign_x, curr_pos.y)
                pos_dy = model.Vec2Double(curr_pos.x, curr_pos.y + sign_y)
                if Calc.distance_sqr(pos_dx, nearest_enemy.position) <= Calc.distance_sqr(pos_dy, nearest_enemy.position):
                    curr_pos.x += sign_x
                else:
                    curr_pos.y += sign_y

                if game.level.tiles[int(curr_pos.x)][int(curr_pos.y)] == model.Tile.WALL:
                    los = False
                    break

        return aim, los

    def calc_shoot(self, los):
        if los:
            if (self.shoot_counter * 5) > self.rltv_enm_dist:
                self.shoot_counter = 0
                return True
        self.shoot_counter += 1
        return False

    def calc_jump(self, unit, game, target_pos):
        jump = True
        if target_pos.y < unit.position.y and game.level.tiles[int(unit.position.x)][int(unit.position.y - 1)] == model.Tile.PLATFORM:
            move_side = Calc.sign(target_pos.x - unit.position.x)
            if game.level.tiles[int(unit.position.x + move_side)][int(unit.position.y)] != model.Tile.WALL:
                if game.level.tiles[int(unit.position.x + move_side)][int(unit.position.y - 1)] != model.Tile.WALL:
                    jump = False
        return jump

    def calc_plant_mine(self, unit, nearest_enemy, velocity, jump, jump_down, los):
        plant_mine = False
        # if (not los) and unit.mines:
        #    if Calc.sign(velocity) == self.rltv_enm_side:
        #        plant_mine = True
        #        jump = False
        #        jump_down = False
        # if unit.mines:
        #    enemy_pos = Calc.sign(nearest_enemy.position.x - unit.position.x)
        #    if Calc.sign(velocity) != enemy_pos:
        #        plant_mine = True
        return plant_mine, jump, jump_down

    def get_action(self, unit, game, debug):
        nearest_enemy, nearest_weapon, nearest_hpbox, nearest_mine, expected_enemy_pos = self.calc_objects(
            unit, game)

        target_pos, velocity = self.calc_move(
            unit, nearest_weapon, nearest_enemy, nearest_hpbox, nearest_mine)

        aim, los = self.calc_aim(
            nearest_enemy, unit, game)

        shoot = self.calc_shoot(los)

        jump = self.calc_jump(unit, game, target_pos)
        jump_down = not jump

        plant_mine, jump, jump_down = self.calc_plant_mine(
            unit, nearest_enemy, velocity, jump, jump_down, los)

        #  Debug----------------------
        # if unit.weapon is not None:
        #    debug.draw(model.CustomData.Log(
        #        "Magazine: {}".format(unit.weapon.magazine)))
        #    debug.draw(model.CustomData.Log(
        #        "Fire timer: {}".format(unit.weapon.fire_timer)))
        #    debug.draw(model.CustomData.Log(
        #        "Last fire tick: {}".format(unit.weapon.last_fire_tick)))
        # debug.draw(model.CustomData.Log(
        #    "Shoot Counter: {}".format(self.shoot_counter)))
        # debug.draw(model.CustomData.Log(
        #     "rltv_dist: {}".format(self.rltv_enm_dist)))
        # debug.draw(model.CustomData.Log(
        #    "rltv_side: {}".format(self.rltv_enm_side)))
        #
        #    debug.draw(model.CustomData.Log(
        #        "Weapon: {}".format(unit.weapon.typ)))
        # debug.draw(model.CustomData.Log("mines: {}".format(unit.mines)))
        # debug.draw(model.CustomData.Log("plant_mine: {}".format(plant_mine)))
        # debug.draw(model.CustomData.Log(
        #    "Nearest Mine: {}".format(nearest_mine)))
        # debug.draw(model.CustomData.Log("Max HP: {}".format(self.max_hp)))
        # debug.draw(model.CustomData.Log("Current HP: {}".format(self.curr_hp)))
        # debug.draw(model.CustomData.Log("My velocity: {}".format(velocity)))
        # debug.draw(model.CustomData.Log(
        #     "Enemy velocity: {}".format(self.enemy_velocity)))
        # debug.draw(model.CustomData.Log("Target pos: {}".format(target_pos)))
        # debug.draw(model.CustomData.Log("Unit pos: {}".format(unit.position)))
        # debug.draw(model.CustomData.Log(
        #     "Enemy pos: {}".format(nearest_enemy.position)))
        # debug.draw(model.CustomData.Log(
        #     "Expected enemy pos: {}".format(expected_enemy_pos)))
        # debug.draw(model.CustomData.Log(
        #    "Velocity: {}".format(target_pos.x - unit.position.x)))
        # debug.draw(model.CustomData.Log("Jump: {}".format(jump)))
        # debug.draw(model.CustomData.Log("Dist X: {}".format(
        #    nearest_enemy.position.x - unit.position.x)))
        # debug.draw(model.CustomData.Log("Dist Y: {}".format(
        #    nearest_enemy.position.y - unit.position.y)))
        # debug.draw(model.CustomData.Log("Trajectory length: {}".format(leng)))
        # debug.draw(model.CustomData.Log(
        #     "poslist: {}".format(poslist)))
        #  /Debug----------------------

        self.prev_enemy_pos = nearest_enemy.position

        return model.UnitAction(
            velocity=velocity,
            jump=jump,
            jump_down=jump_down,
            aim=aim,
            shoot=shoot,
            reload=False,
            swap_weapon=self.swap_weapon,
            plant_mine=plant_mine and not shoot)
