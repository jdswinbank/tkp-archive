SET SCHEMA pipeline;

DROP FUNCTION GetDatasetId;

CREATE FUNCTION GetDatasetId() RETURNS INT
BEGIN
  RETURN SELECT NEXT VALUE FOR seq_datasets;
END;


