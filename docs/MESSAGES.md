# Message

<i id="">path: #</i>

# definitions

**_Position_**

 - ## Position
 - Type: `object`
 - <i id="/definitions/Position">path: #/definitions/Position</i>
 - **_Properties_**
	 - <b id="#/definitions/Position/properties/x">x</b> `required`
		 - #### X
		 - Type: `integer`
		 - <i id="/definitions/Position/properties/x">path: #/definitions/Position/properties/x</i>
	 - <b id="#/definitions/Position/properties/y">y</b> `required`
		 - #### Y
		 - Type: `integer`
		 - <i id="/definitions/Position/properties/y">path: #/definitions/Position/properties/y</i>


**_PlayerPiecePosition_**

 - ## PlayerPiecePosition
 - Type: `object`
 - <i id="/definitions/PlayerPiecePosition">path: #/definitions/PlayerPiecePosition</i>
 - **_Properties_**
	 - <b id="#/definitions/PlayerPiecePosition/properties/player_id">player_id</b> `required`
		 - #### Player Id
		 - Type: `string`
		 - <i id="/definitions/PlayerPiecePosition/properties/player_id">path: #/definitions/PlayerPiecePosition/properties/player_id</i>
		 - String format must be a "uuid"
	 - <b id="#/definitions/PlayerPiecePosition/properties/piece_id">piece_id</b> `required`
		 - #### Piece Id
		 - Type: `string`
		 - <i id="/definitions/PlayerPiecePosition/properties/piece_id">path: #/definitions/PlayerPiecePosition/properties/piece_id</i>
		 - String format must be a "uuid"
	 - <b id="#/definitions/PlayerPiecePosition/properties/position">position</b> `required`
		 - <i id="/definitions/PlayerPiecePosition/properties/position">path: #/definitions/PlayerPiecePosition/properties/position</i>
		 - &#36;ref: [#/definitions/Position](#/definitions/Position)


**_RoundStartPayload_**

 - ## RoundStartPayload
 - Type: `object`
 - <i id="/definitions/RoundStartPayload">path: #/definitions/RoundStartPayload</i>
 - **_Properties_**
	 - <b id="#/definitions/RoundStartPayload/properties/round_number">round_number</b> `required`
		 - #### Round Number
		 - Type: `integer`
		 - <i id="/definitions/RoundStartPayload/properties/round_number">path: #/definitions/RoundStartPayload/properties/round_number</i>
	 - <b id="#/definitions/RoundStartPayload/properties/round_duration">round_duration</b> `required`
		 - #### Round Duration
		 - Type: `number`
		 - <i id="/definitions/RoundStartPayload/properties/round_duration">path: #/definitions/RoundStartPayload/properties/round_duration</i>
	 - <b id="#/definitions/RoundStartPayload/properties/board_state">board_state</b> `required`
		 - #### Board State
		 - Type: `array`
		 - <i id="/definitions/RoundStartPayload/properties/board_state">path: #/definitions/RoundStartPayload/properties/board_state</i>
			 - **_Items_**
			 - <i id="/definitions/RoundStartPayload/properties/board_state/items">path: #/definitions/RoundStartPayload/properties/board_state/items</i>
			 - &#36;ref: [#/definitions/PlayerPiecePosition](#/definitions/PlayerPiecePosition)


**_RoundStartMessage_**

 - ## RoundStartMessage
 - Type: `object`
 - <i id="/definitions/RoundStartMessage">path: #/definitions/RoundStartMessage</i>
 - **_Properties_**
	 - <b id="#/definitions/RoundStartMessage/properties/type">type</b> `required`
		 - #### Type
		 - Type: `string`
		 - <i id="/definitions/RoundStartMessage/properties/type">path: #/definitions/RoundStartMessage/properties/type</i>
		 - The value is restricted to the following: 
			 1. _"round_start"_
	 - <b id="#/definitions/RoundStartMessage/properties/payload">payload</b> `required`
		 - <i id="/definitions/RoundStartMessage/properties/payload">path: #/definitions/RoundStartMessage/properties/payload</i>
		 - &#36;ref: [#/definitions/RoundStartPayload](#/definitions/RoundStartPayload)


**_PieceAction_**

 - ## PieceAction
 - _An enumeration._
 - Type: `string`
 - <i id="/definitions/PieceAction">path: #/definitions/PieceAction</i>
 - The value is restricted to the following: 
	 1. _"no_action"_
	 2. _"move_up"_
	 3. _"move_down"_
	 4. _"move_left"_
	 5. _"move_right"_


**_TimelineEventAction_**

 - ## TimelineEventAction
 - Type: `object`
 - <i id="/definitions/TimelineEventAction">path: #/definitions/TimelineEventAction</i>
 - **_Properties_**
	 - <b id="#/definitions/TimelineEventAction/properties/player_id">player_id</b> `required`
		 - #### Player Id
		 - Type: `string`
		 - <i id="/definitions/TimelineEventAction/properties/player_id">path: #/definitions/TimelineEventAction/properties/player_id</i>
		 - String format must be a "uuid"
	 - <b id="#/definitions/TimelineEventAction/properties/piece_id">piece_id</b> `required`
		 - #### Piece Id
		 - Type: `string`
		 - <i id="/definitions/TimelineEventAction/properties/piece_id">path: #/definitions/TimelineEventAction/properties/piece_id</i>
		 - String format must be a "uuid"
	 - <b id="#/definitions/TimelineEventAction/properties/action">action</b> `required`
		 - <i id="/definitions/TimelineEventAction/properties/action">path: #/definitions/TimelineEventAction/properties/action</i>
		 - &#36;ref: [#/definitions/PieceAction](#/definitions/PieceAction)


**_MoveOutcomePayload_**

 - ## MoveOutcomePayload
 - Type: `object`
 - <i id="/definitions/MoveOutcomePayload">path: #/definitions/MoveOutcomePayload</i>
 - **_Properties_**
	 - <b id="#/definitions/MoveOutcomePayload/properties/piece_id">piece_id</b> `required`
		 - #### Piece Id
		 - Type: `string`
		 - <i id="/definitions/MoveOutcomePayload/properties/piece_id">path: #/definitions/MoveOutcomePayload/properties/piece_id</i>
		 - String format must be a "uuid"
	 - <b id="#/definitions/MoveOutcomePayload/properties/off_board">off_board</b> `required`
		 - #### Off Board
		 - Type: `boolean`
		 - <i id="/definitions/MoveOutcomePayload/properties/off_board">path: #/definitions/MoveOutcomePayload/properties/off_board</i>
	 - <b id="#/definitions/MoveOutcomePayload/properties/new_position">new_position</b> `required`
		 - <i id="/definitions/MoveOutcomePayload/properties/new_position">path: #/definitions/MoveOutcomePayload/properties/new_position</i>
		 - &#36;ref: [#/definitions/Position](#/definitions/Position)


**_MoveOutcome_**

 - ## MoveOutcome
 - Type: `object`
 - <i id="/definitions/MoveOutcome">path: #/definitions/MoveOutcome</i>
 - **_Properties_**
	 - <b id="#/definitions/MoveOutcome/properties/type">type</b> `required`
		 - #### Type
		 - Type: `string`
		 - <i id="/definitions/MoveOutcome/properties/type">path: #/definitions/MoveOutcome/properties/type</i>
		 - The value is restricted to the following: 
			 1. _"move"_
	 - <b id="#/definitions/MoveOutcome/properties/payload">payload</b> `required`
		 - <i id="/definitions/MoveOutcome/properties/payload">path: #/definitions/MoveOutcome/properties/payload</i>
		 - &#36;ref: [#/definitions/MoveOutcomePayload](#/definitions/MoveOutcomePayload)


**_MoveConflictOutcomePayload_**

 - ## MoveConflictOutcomePayload
 - Type: `object`
 - <i id="/definitions/MoveConflictOutcomePayload">path: #/definitions/MoveConflictOutcomePayload</i>
 - **_Properties_**
	 - <b id="#/definitions/MoveConflictOutcomePayload/properties/piece_ids">piece_ids</b> `required`
		 - #### Piece Ids
		 - Type: `array`
		 - <i id="/definitions/MoveConflictOutcomePayload/properties/piece_ids">path: #/definitions/MoveConflictOutcomePayload/properties/piece_ids</i>
			 - **_Items_**
			 - Type: `string`
			 - <i id="/definitions/MoveConflictOutcomePayload/properties/piece_ids/items">path: #/definitions/MoveConflictOutcomePayload/properties/piece_ids/items</i>
			 - String format must be a "uuid"
	 - <b id="#/definitions/MoveConflictOutcomePayload/properties/collision_point">collision_point</b> `required`
		 - <i id="/definitions/MoveConflictOutcomePayload/properties/collision_point">path: #/definitions/MoveConflictOutcomePayload/properties/collision_point</i>
		 - &#36;ref: [#/definitions/Position](#/definitions/Position)


**_MoveConflictOutcome_**

 - ## MoveConflictOutcome
 - Type: `object`
 - <i id="/definitions/MoveConflictOutcome">path: #/definitions/MoveConflictOutcome</i>
 - **_Properties_**
	 - <b id="#/definitions/MoveConflictOutcome/properties/type">type</b> `required`
		 - #### Type
		 - Type: `string`
		 - <i id="/definitions/MoveConflictOutcome/properties/type">path: #/definitions/MoveConflictOutcome/properties/type</i>
		 - The value is restricted to the following: 
			 1. _"move_conflict"_
	 - <b id="#/definitions/MoveConflictOutcome/properties/payload">payload</b> `required`
		 - <i id="/definitions/MoveConflictOutcome/properties/payload">path: #/definitions/MoveConflictOutcome/properties/payload</i>
		 - &#36;ref: [#/definitions/MoveConflictOutcomePayload](#/definitions/MoveConflictOutcomePayload)


**_Direction_**

 - ## Direction
 - _An enumeration._
 - Type: `string`
 - <i id="/definitions/Direction">path: #/definitions/Direction</i>
 - The value is restricted to the following: 
	 1. _"up"_
	 2. _"down"_
	 3. _"left"_
	 4. _"right"_


**_PushOutcomePayload_**

 - ## PushOutcomePayload
 - Type: `object`
 - <i id="/definitions/PushOutcomePayload">path: #/definitions/PushOutcomePayload</i>
 - **_Properties_**
	 - <b id="#/definitions/PushOutcomePayload/properties/pusher_piece_id">pusher_piece_id</b> `required`
		 - #### Pusher Piece Id
		 - Type: `string`
		 - <i id="/definitions/PushOutcomePayload/properties/pusher_piece_id">path: #/definitions/PushOutcomePayload/properties/pusher_piece_id</i>
		 - String format must be a "uuid"
	 - <b id="#/definitions/PushOutcomePayload/properties/victim_piece_ids">victim_piece_ids</b> `required`
		 - #### Victim Piece Ids
		 - Type: `array`
		 - <i id="/definitions/PushOutcomePayload/properties/victim_piece_ids">path: #/definitions/PushOutcomePayload/properties/victim_piece_ids</i>
			 - **_Items_**
			 - Type: `string`
			 - <i id="/definitions/PushOutcomePayload/properties/victim_piece_ids/items">path: #/definitions/PushOutcomePayload/properties/victim_piece_ids/items</i>
			 - String format must be a "uuid"
	 - <b id="#/definitions/PushOutcomePayload/properties/direction">direction</b> `required`
		 - <i id="/definitions/PushOutcomePayload/properties/direction">path: #/definitions/PushOutcomePayload/properties/direction</i>
		 - &#36;ref: [#/definitions/Direction](#/definitions/Direction)


**_PushOutcome_**

 - ## PushOutcome
 - Type: `object`
 - <i id="/definitions/PushOutcome">path: #/definitions/PushOutcome</i>
 - **_Properties_**
	 - <b id="#/definitions/PushOutcome/properties/type">type</b> `required`
		 - #### Type
		 - Type: `string`
		 - <i id="/definitions/PushOutcome/properties/type">path: #/definitions/PushOutcome/properties/type</i>
		 - The value is restricted to the following: 
			 1. _"push"_
	 - <b id="#/definitions/PushOutcome/properties/payload">payload</b> `required`
		 - <i id="/definitions/PushOutcome/properties/payload">path: #/definitions/PushOutcome/properties/payload</i>
		 - &#36;ref: [#/definitions/PushOutcomePayload](#/definitions/PushOutcomePayload)


**_PushConflictOutcomePayload_**

 - ## PushConflictOutcomePayload
 - Type: `object`
 - <i id="/definitions/PushConflictOutcomePayload">path: #/definitions/PushConflictOutcomePayload</i>
 - **_Properties_**
	 - <b id="#/definitions/PushConflictOutcomePayload/properties/piece_a">piece_a</b> `required`
		 - #### Piece A
		 - Type: `string`
		 - <i id="/definitions/PushConflictOutcomePayload/properties/piece_a">path: #/definitions/PushConflictOutcomePayload/properties/piece_a</i>
		 - String format must be a "uuid"
	 - <b id="#/definitions/PushConflictOutcomePayload/properties/piece_b">piece_b</b> `required`
		 - #### Piece B
		 - Type: `string`
		 - <i id="/definitions/PushConflictOutcomePayload/properties/piece_b">path: #/definitions/PushConflictOutcomePayload/properties/piece_b</i>
		 - String format must be a "uuid"


**_PushConflictOutcome_**

 - ## PushConflictOutcome
 - Type: `object`
 - <i id="/definitions/PushConflictOutcome">path: #/definitions/PushConflictOutcome</i>
 - **_Properties_**
	 - <b id="#/definitions/PushConflictOutcome/properties/type">type</b> `required`
		 - #### Type
		 - Type: `string`
		 - <i id="/definitions/PushConflictOutcome/properties/type">path: #/definitions/PushConflictOutcome/properties/type</i>
		 - The value is restricted to the following: 
			 1. _"push_conflict"_
	 - <b id="#/definitions/PushConflictOutcome/properties/payload">payload</b> `required`
		 - <i id="/definitions/PushConflictOutcome/properties/payload">path: #/definitions/PushConflictOutcome/properties/payload</i>
		 - &#36;ref: [#/definitions/PushConflictOutcomePayload](#/definitions/PushConflictOutcomePayload)


**_Outcome_**

 - ## Outcome
 - <i id="/definitions/Outcome">path: #/definitions/Outcome</i>


**_TimelineEvent_**

 - ## TimelineEvent
 - Type: `object`
 - <i id="/definitions/TimelineEvent">path: #/definitions/TimelineEvent</i>
 - **_Properties_**
	 - <b id="#/definitions/TimelineEvent/properties/actions">actions</b> `required`
		 - #### Actions
		 - Type: `array`
		 - <i id="/definitions/TimelineEvent/properties/actions">path: #/definitions/TimelineEvent/properties/actions</i>
			 - **_Items_**
			 - <i id="/definitions/TimelineEvent/properties/actions/items">path: #/definitions/TimelineEvent/properties/actions/items</i>
			 - &#36;ref: [#/definitions/TimelineEventAction](#/definitions/TimelineEventAction)
	 - <b id="#/definitions/TimelineEvent/properties/outcomes">outcomes</b> `required`
		 - #### Outcomes
		 - Type: `array`
		 - <i id="/definitions/TimelineEvent/properties/outcomes">path: #/definitions/TimelineEvent/properties/outcomes</i>
			 - **_Items_**
			 - <i id="/definitions/TimelineEvent/properties/outcomes/items">path: #/definitions/TimelineEvent/properties/outcomes/items</i>
			 - &#36;ref: [#/definitions/Outcome](#/definitions/Outcome)


**_GameOver_**

 - ## GameOver
 - Type: `object`
 - <i id="/definitions/GameOver">path: #/definitions/GameOver</i>
 - **_Properties_**
	 - <b id="#/definitions/GameOver/properties/winner_player_id">winner_player_id</b>
		 - #### Winner Player Id
		 - Type: `string`
		 - <i id="/definitions/GameOver/properties/winner_player_id">path: #/definitions/GameOver/properties/winner_player_id</i>
		 - String format must be a "uuid"


**_RoundResultPayload_**

 - ## RoundResultPayload
 - Type: `object`
 - <i id="/definitions/RoundResultPayload">path: #/definitions/RoundResultPayload</i>
 - **_Properties_**
	 - <b id="#/definitions/RoundResultPayload/properties/timeline">timeline</b> `required`
		 - #### Timeline
		 - Type: `array`
		 - <i id="/definitions/RoundResultPayload/properties/timeline">path: #/definitions/RoundResultPayload/properties/timeline</i>
			 - **_Items_**
			 - <i id="/definitions/RoundResultPayload/properties/timeline/items">path: #/definitions/RoundResultPayload/properties/timeline/items</i>
			 - &#36;ref: [#/definitions/TimelineEvent](#/definitions/TimelineEvent)
	 - <b id="#/definitions/RoundResultPayload/properties/game_over">game_over</b>
		 - <i id="/definitions/RoundResultPayload/properties/game_over">path: #/definitions/RoundResultPayload/properties/game_over</i>
		 - &#36;ref: [#/definitions/GameOver](#/definitions/GameOver)


**_RoundResultMessage_**

 - ## RoundResultMessage
 - Type: `object`
 - <i id="/definitions/RoundResultMessage">path: #/definitions/RoundResultMessage</i>
 - **_Properties_**
	 - <b id="#/definitions/RoundResultMessage/properties/type">type</b> `required`
		 - #### Type
		 - Type: `string`
		 - <i id="/definitions/RoundResultMessage/properties/type">path: #/definitions/RoundResultMessage/properties/type</i>
		 - The value is restricted to the following: 
			 1. _"round_result"_
	 - <b id="#/definitions/RoundResultMessage/properties/payload">payload</b> `required`
		 - <i id="/definitions/RoundResultMessage/properties/payload">path: #/definitions/RoundResultMessage/properties/payload</i>
		 - &#36;ref: [#/definitions/RoundResultPayload](#/definitions/RoundResultPayload)


**_PlayerMove_**

 - ## PlayerMove
 - Type: `object`
 - <i id="/definitions/PlayerMove">path: #/definitions/PlayerMove</i>
 - **_Properties_**
	 - <b id="#/definitions/PlayerMove/properties/piece_id">piece_id</b> `required`
		 - #### Piece Id
		 - Type: `string`
		 - <i id="/definitions/PlayerMove/properties/piece_id">path: #/definitions/PlayerMove/properties/piece_id</i>
		 - String format must be a "uuid"
	 - <b id="#/definitions/PlayerMove/properties/action">action</b> `required`
		 - <i id="/definitions/PlayerMove/properties/action">path: #/definitions/PlayerMove/properties/action</i>
		 - &#36;ref: [#/definitions/PieceAction](#/definitions/PieceAction)


**_PlayerMovesPayload_**

 - ## PlayerMovesPayload
 - Type: `object`
 - <i id="/definitions/PlayerMovesPayload">path: #/definitions/PlayerMovesPayload</i>
 - **_Properties_**
	 - <b id="#/definitions/PlayerMovesPayload/properties/moves">moves</b> `required`
		 - #### Moves
		 - Type: `array`
		 - <i id="/definitions/PlayerMovesPayload/properties/moves">path: #/definitions/PlayerMovesPayload/properties/moves</i>
			 - **_Items_**
			 - <i id="/definitions/PlayerMovesPayload/properties/moves/items">path: #/definitions/PlayerMovesPayload/properties/moves/items</i>
			 - &#36;ref: [#/definitions/PlayerMove](#/definitions/PlayerMove)


**_PlayerMovesMessage_**

 - ## PlayerMovesMessage
 - Type: `object`
 - <i id="/definitions/PlayerMovesMessage">path: #/definitions/PlayerMovesMessage</i>
 - **_Properties_**
	 - <b id="#/definitions/PlayerMovesMessage/properties/type">type</b> `required`
		 - #### Type
		 - Type: `string`
		 - <i id="/definitions/PlayerMovesMessage/properties/type">path: #/definitions/PlayerMovesMessage/properties/type</i>
		 - The value is restricted to the following: 
			 1. _"player_moves"_
	 - <b id="#/definitions/PlayerMovesMessage/properties/payload">payload</b> `required`
		 - <i id="/definitions/PlayerMovesMessage/properties/payload">path: #/definitions/PlayerMovesMessage/properties/payload</i>
		 - &#36;ref: [#/definitions/PlayerMovesPayload](#/definitions/PlayerMovesPayload)


**_ReadyForNextRoundPayload_**

 - ## ReadyForNextRoundPayload
 - Type: `object`
 - <i id="/definitions/ReadyForNextRoundPayload">path: #/definitions/ReadyForNextRoundPayload</i>
 - **_Properties_**


**_ReadyForNextRoundMessage_**

 - ## ReadyForNextRoundMessage
 - Type: `object`
 - <i id="/definitions/ReadyForNextRoundMessage">path: #/definitions/ReadyForNextRoundMessage</i>
 - **_Properties_**
	 - <b id="#/definitions/ReadyForNextRoundMessage/properties/type">type</b> `required`
		 - #### Type
		 - Type: `string`
		 - <i id="/definitions/ReadyForNextRoundMessage/properties/type">path: #/definitions/ReadyForNextRoundMessage/properties/type</i>
		 - The value is restricted to the following: 
			 1. _"ready_for_next_round"_
	 - <b id="#/definitions/ReadyForNextRoundMessage/properties/payload">payload</b>
		 - <i id="/definitions/ReadyForNextRoundMessage/properties/payload">path: #/definitions/ReadyForNextRoundMessage/properties/payload</i>
		 - &#36;ref: [#/definitions/ReadyForNextRoundPayload](#/definitions/ReadyForNextRoundPayload)



_Generated with [json-schema-md-doc](https://brianwendt.github.io/json-schema-md-doc/)_
