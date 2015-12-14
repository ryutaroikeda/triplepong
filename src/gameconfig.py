class GameConfig:
    player_size = 3
    game_length = 120.0
    frames_per_sec = 60.0
    screen_width = 640
    screen_height = 480
    buffer_region = 50
    ball_wall_offset_x = 8
    ball_wall_offset_y = 40
    paddle_offset = 60
    paddle_width = 16
    paddle_height = 60
    ball_vel = 4
    ball_size = 8
    rounds = 2
    rotation_length = ((game_length / rounds) * frames_per_sec) // \
            player_size
    round_length = rotation_length * player_size

    def Apply(self, s):
        '''Apply the configuration to a game state.
        Argument:
        s -- The game state to configure.
        '''
        buffer_region = self.buffer_region
        ball_wall_offset_x = self.ball_wall_offset_x
        ball_wall_offset_y = self.ball_wall_offset_y
        paddle_offset = self.paddle_offset
        paddle_half_width = self.paddle_width // 2
        paddle_half_height = self.paddle_height // 2
        ball_vel = self.ball_vel
        ball_half_size = self.ball_size // 2
        s.player_size = self.player_size
        s.game_length = self.game_length
        s.frames_per_sec = self.frame_rate
        s.rounds = self.rounds
        s.rotation_length = ((s.game_length / s.rounds) * \
                s.frames_per_sec) // s.player_size
        s.round_length = s.rotation_length * s.player_size
        s.screen.half_width = self.screen_width // 2
        s.screen.half_height = self.screen_height // 2
        s.goal_left.pos_x = - buffer_region
        s.goal_left.pos_y = s.screen.half_height
        s.goal_left.half_width = buffer_region
        s.goal_left.half_height = 100 *  s.screen.half_height
        s.goal_right.pos_x = 2 * s.screen.half_width + buffer_region
        s.goal_right.pos_y = s.screen.half_height
        s.goal_right.half_width = buffer_region
        s.goal_right.half_height = 100 * s.screen.half_height
        s.ball_wall_top.pos_x = s.screen.half_width
        s.ball_wall_top.pos_y = - buffer_region + ball_wall_offset_y
        s.ball_wall_top.half_width = (s.screen.half_width - \
                paddle_offset - paddle_half_width - ball_wall_offset_x)
        s.ball_wall_top.half_height = buffer_region
        s.ball_wall_bottom.pos_x = s.screen.half_width
        s.ball_wall_bottom.pos_y = (2 * s.screen.half_height + \
                buffer_region - ball_wall_offset_y)
        s.ball_wall_bottom.half_width = (s.screen.half_width - \
                paddle_offset - paddle_half_width - ball_wall_offset_x)
        s.ball_wall_bottom.half_height = buffer_region
        s.paddle_wall_top.pos_x = s.screen.half_width
        s.paddle_wall_top.pos_y = - buffer_region
        s.paddle_wall_top.half_width = 2 * s.screen.half_width
        s.paddle_wall_top.half_height = buffer_region
        s.paddle_wall_bottom.pos_x = s.screen.half_width
        s.paddle_wall_bottom.pos_y = (2 * s.screen.half_height + \
                buffer_region)
        s.paddle_wall_bottom.half_width = 2 * s.screen.half_width
        s.paddle_wall_bottom.half_height = buffer_region
        s.ball.pos_x = s.screen.half_width
        s.ball.pos_y = s.screen.half_height
        s.ball.vel_x = -ball_vel
        s.ball.vel_y = 0
        s.ball.half_width = ball_half_size
        s.ball.half_height = ball_half_size
        s.paddle_left.pos_x = paddle_offset
        s.paddle_left.pos_y = 0
        s.paddle_left.vel_x = 0
        s.paddle_left.vel_y = 0
        s.paddle_left.half_width = paddle_half_width
        s.paddle_left.half_height = paddle_half_height
        s.paddle_right.pos_x = 2 * s.screen.half_width - paddle_offset 
        s.paddle_right.pos_y = 0
        s.paddle_right.vel_x = 0
        s.paddle_right.vel_y = 0
        s.paddle_right.half_width = paddle_half_width
        s.paddle_right.half_height = paddle_half_height
    def Serialize(self):
        pass
    def Deserialize(self):
        pass

