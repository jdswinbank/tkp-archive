USE pipeline;

INSERT INTO catalogues
  (catid
  ,catname
  ,fullname
  ) VALUES 
  (8
  ,'VLSS'
  ,'The VLA Low-frequency Sky Survey at 74MHz, The VLSS Catalog, Version 2007-06-26'
  )
;

LOAD DATA INFILE '/scratch/bscheers/databases/catalogues/vlss/csv/vlss-0-68311-all.csv'
INTO TABLE cataloguesources 
FIELDS TERMINATED BY ';' 
LINES TERMINATED BY '\n' 
  (@viz_RAJ2000
  ,@viz_DEJ2000
  ,@orig_catsrcid
  ,@name
  ,@RA
  ,@e_RA
  ,@decl
  ,@e_decl
  ,@Si
  ,@e_Si
  ,@l_MajAx
  ,@MajAx
  ,@e_MajAx
  ,@l_MinAx
  ,@MinAx
  ,@e_MinAx
  ,@PA
  ,@e_PA
  ,@dummy
  ,@dummy
  ,@dummy
  ,@dummy
  ) 
SET 
   orig_catsrcid = @orig_catsrcid
  ,catsrcname = @name 
  ,cat_id = 8
  ,band = 1
  ,freq_eff = 74000000
  ,ra = @viz_RAJ2000
  ,decl = @viz_DEJ2000
  ,zone = FLOOR(decl)
  ,ra_err = @e_ra / 240 -- errors are given in sec
  ,decl_err = @e_decl / 3600
  ,x = COS(RADIANS(decl)) * COS(RADIANS(ra))
  ,y = COS(RADIANS(decl)) * SIN(RADIANS(ra))
  ,z = SIN(RADIANS(decl))
  ,i_int_avg = @Si
  ,i_int_avg_err = @e_Si
;

