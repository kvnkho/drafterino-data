SELECT
public_matches.match_id,
public_matches.start_time,
public_matches.radiant_win win,
public_player_matches.hero_id,
second_player.hero_id as teammate
FROM public_player_matches
INNER JOIN public_player_matches second_player using(match_id)
LEFT JOIN public_matches using(match_id)
WHERE TRUE
AND public_player_matches.player_slot < 128
AND second_player.player_slot < 128
AND public_player_matches.hero_id = 1
AND second_player.hero_id = 3
AND public_matches.start_time >= (extract(epoch from now()) - (86400 * 2))
AND public_matches.start_time <= (extract(epoch from now()) - (86400 * 1.5))
LIMIT 60