USE pipeline;

DROP FUNCTION IF EXISTS testBoolean;

DELIMITER //

CREATE FUNCTION testBoolean(ia INT) RETURNS BOOLEAN
DETERMINISTIC
BEGIN
  DECLARE obool BOOLEAN DEFAULT NULL;

  IF ia >= 0 THEN
    SET obool = TRUE;
  END IF;

  RETURN obool;

END;
//

DELIMITER ;

