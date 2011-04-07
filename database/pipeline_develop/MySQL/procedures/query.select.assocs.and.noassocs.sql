SET @image_id = 1;
SET @zoneheight = 1;
SET @theta = 1;


SET  @cnt = 0;

/*
select
== assocs ==
union
select
== no assocs for sources in current image ==
union
select
== no assocs in case of empty table ==
;

 * Select 1:
 * sources with assocs 
 * Select 2: 
 * Query to select new sources in current image
 * i.e. no associations could be found in associatedsources.
 * (or: all sources from image_id = @image_id that do NOT intersect with sources 
 * from images with the same ds_id as @image_id)
 */


select x2.xtrsrcid AS xtrsrc_id
      ,FALSE AS insert_src1
      ,'X' as assoc_type
      ,x1.xtrsrcid AS assoc_xtrsrc_id
      ,CASE WHEN (@cnt := @cnt + 1) = 1
            THEN TRUE
            ELSE FALSE
            END AS insert_src2
  from extractedsources x1
      ,images im1
      ,associatedsources a1
      ,extractedsources x2
      ,images im2
 where exists (select a3.xtrsrc_id
                 from associatedsources a3
                     ,extractedsources x3
                     ,images im3
                where x3.xtrsrcid = a3.xtrsrc_id
                  and x3.image_id = im3.imageid
                  and im3.ds_id = (select im10.ds_id
                                     from images im10
                                    where imageid = @image_id
                                  )
              )
   and x1.image_id = @image_id
   AND x1.image_id = im1.imageid
   AND im1.ds_id = (SELECT im11.ds_id
                      FROM images im11
                     WHERE im11.imageid = @image_id
                   )
   and a1.xtrsrc_id = x2.xtrsrcid
   and x2.image_id = im2.imageid
   and im1.ds_id = im2.ds_id
   AND x2.zone BETWEEN FLOOR((x1.decl - @theta) / @zoneheight)                    
                   AND FLOOR((x1.decl + @theta) / @zoneheight)    
   AND x2.ra BETWEEN (x1.ra - alpha(@theta,x1.decl))                  
                 AND (x1.ra + alpha(@theta,x1.decl))    
   AND x2.decl BETWEEN x1.decl - @theta
                   AND x1.decl + @theta 
   AND doSourcesIntersect(x1.ra,x1.decl,x1.ra_err,x1.decl_err
                         ,x2.ra,x2.decl,x2.ra_err,x2.decl_err)
union
select x1.xtrsrcid AS xtrsrc_id
      ,TRUE AS insert_src1
      ,'X' AS assoc_type
      ,x1.xtrsrcid AS assoc_xtrsrc_id
      ,FALSE AS insert_src2
  from extractedsources x1
      ,associatedsources a1
      ,extractedsources x2
      ,images im2 
 where x1.image_id = @image_id 
   and a1.xtrsrc_id = x2.xtrsrcid 
   and x2.image_id = im2.imageid 
   and im2.ds_id = (select ds_id 
                      from images im3 
                     where imageid = @image_id
                   ) 
   and not doSourcesIntersect(x1.ra,x1.decl,x1.ra_err,x1.decl_err
                             ,x2.ra,x2.decl,x2.ra_err,x2.decl_err)
   and x1.xtrsrcid not in (SELECT x3.xtrsrcid       
                             FROM extractedsources x3       
                                 ,images im4       
                                 ,associatedsources a2       
                                 ,extractedsources x4       
                                 ,images im5  
                            WHERE x3.image_id = @image_id    
                              AND x3.image_id = im4.imageid    
                              AND im4.ds_id = (SELECT im6.ds_id                       
                                                 FROM images im6                      
                                                WHERE im6.imageid = @image_id                    
                                              )    
                              AND a2.xtrsrc_id = x4.xtrsrcid    
                              AND x4.image_id = im5.imageid    
                              AND im5.ds_id = im4.ds_id    
                              AND x4.zone BETWEEN FLOOR((x3.decl - @theta) / @zoneheight) 
                                              AND FLOOR((x3.decl + @theta) / @zoneheight)   
                              AND x4.ra BETWEEN (x3.ra - alpha(@theta,x3.decl))
                                            AND (x3.ra + alpha(@theta,x3.decl))    
                              AND x4.decl BETWEEN x3.decl - @theta
                                              AND x3.decl + @theta 
                              AND doSourcesIntersect(x3.ra,x3.decl,x3.ra_err,x3.decl_err
                                                    ,x4.ra,x4.decl,x4.ra_err,x4.decl_err)
                          )
GROUP BY x1.xtrsrcid
union
select x1.xtrsrcid
      ,TRUE AS insert_src1
      ,'X' AS assoc_type
      ,x1.xtrsrcid AS assoc_xtrsrc_id
      ,FALSE AS insert_src2
  from extractedsources x1
 where not exists (select a2.xtrsrc_id
                     from associatedsources a2
                         ,extractedsources x2
                         ,images im2
                    where x2.xtrsrcid = a2.xtrsrc_id
                      and x2.image_id = im2.imageid
                      and im2.ds_id = (select im10.ds_id
                                         from images im10
                                        where imageid = @image_id
                                      )
                  )
   and x1.image_id = @image_id
;


stop;

/*sources from image_id = 2 that DO intersect with sources from image_id = 1 */
SELECT x1.xtrsrcid       
      ,x1.image_id       
      ,im1.ds_id       
      ,a1.xtrsrc_id       
      ,x2.xtrsrcid       
      ,doSourcesIntersect(x1.ra,x1.decl,x1.ra_err,x1.decl_err
                         ,x2.ra,x2.decl,x2.ra_err,x2.decl_err
                         ) AS 'do_intersect'   
  FROM extractedsources x1       
      ,images im1       
      ,associatedsources a1       
      ,extractedsources x2       
      ,images im2  
 WHERE x1.image_id = @image_id    
   AND x1.image_id = im1.imageid    
   AND im1.ds_id = (SELECT im3.ds_id                       
                      FROM images im3                      
                     WHERE im3.imageid = @image_id                    
                   )    
   AND a1.xtrsrc_id = x2.xtrsrcid    
   AND x2.image_id = im2.imageid    
   AND im2.ds_id = im1.ds_id    
   AND x2.zone BETWEEN FLOOR((x1.decl - @theta) / @zoneheight)                    
                   AND FLOOR((x1.decl + @theta) / @zoneheight)    
   AND x2.ra BETWEEN (x1.ra - alpha(@theta,x1.decl))                  
                 AND (x1.ra + alpha(@theta,x1.decl))    
   AND x2.decl BETWEEN x1.decl - @theta
                   AND x1.decl + @theta 
   AND doSourcesIntersect(x1.ra,x1.decl,x1.ra_err,x1.decl_err
                         ,x2.ra,x2.decl,x2.ra_err,x2.decl_err)

;


stop;

*/
/* to also select the extracted sources that do not have associations 
* we have to perform an outer join
*/
/*
delete from associatedsources;
alter table associatedsources auto_increment = 1;
delete from extractedsources;
alter table extractedsources auto_increment = 1;
delete from images;
alter table images auto_increment = 1;
delete from datasets;
alter table datasets auto_increment = 1;
*/


/*
SELECT COUNT(*)
  FROM extractedsources x1
      ,images       
      ,datasets       
      ,extractedsources x2       
      ,associatedsources     
 WHERE x1.image_id = imageid    
   AND ds_id = dsid    
   AND dsid = (SELECT ds_id                  
                 FROM images                 
                WHERE imageid = @image_id               
              )    
   AND x1.image_id <> @image_id    
   AND x2.image_id = @image_id    
   AND xtrsrc_id = x2.xtrsrcid    
   AND dosourcesintersect(x1.ra,x1.decl,x1.ra_err,x1.decl_err,x2.ra,x2.decl,x2.ra_err,x2.decl_err)
;

insert into associatedsources 
  (xtrsrc_id
  ,insert_src1
  ,assoc_type
  ,assoc_xtrsrc_id
  ,insert_src2
  ) 
  select xtrsrcid
        ,true
        ,'X'
        ,xtrsrcid
        ,false 
    from extractedsources 
   where image_id = @image_id
;

SELECT x1.xtrsrcid AS xtr
      ,x2.xtrsrcid AS assoc_xtr
  FROM extractedsources x1
      ,images       
      ,datasets       
      ,extractedsources x2       
 WHERE x1.image_id = imageid    
   AND ds_id = dsid    
   AND dsid = (SELECT ds_id                  
                 FROM images                 
                WHERE imageid = @image_id               
              )    
   AND x1.image_id <> @image_id    
   AND x2.image_id = @image_id    
   AND dosourcesintersect(x1.ra,x1.decl,x1.ra_err,x1.decl_err,x2.ra,x2.decl,x2.ra_err,x2.decl_err)
;
*/
