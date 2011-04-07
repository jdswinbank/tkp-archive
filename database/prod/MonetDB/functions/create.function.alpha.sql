--DROP FUNCTION alpha;

/**
 * This function computes the ra expansion for a given theta at 
 * a given declination.
 * theta and decl are both in degrees.
 */
CREATE FUNCTION alpha(theta DOUBLE, decl DOUBLE) RETURNS DOUBLE 
BEGIN
  IF ABS(decl) + theta > 89.9 THEN 
    RETURN 180;
  ELSE 
    RETURN degrees(ABS(ATAN(SIN(radians(theta)) / SQRT(ABS(COS(radians(decl - theta)) * COS(radians(decl + theta))))))) ; 
  END IF ;
END;
