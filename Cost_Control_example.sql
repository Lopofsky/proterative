-- Adminer 4.7.1 PostgreSQL dump

DROP TABLE IF EXISTS "Bank_Deposits";
DROP SEQUENCE IF EXISTS "Bank_Deposits_ID_seq";
CREATE SEQUENCE "Bank_Deposits_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1;

CREATE TABLE "public"."Bank_Deposits" (
    "ID" integer DEFAULT nextval('"Bank_Deposits_ID_seq"') NOT NULL,
    "From" text,
    "To" text,
    "Meta" jsonb,
    "Amount" numeric NOT NULL,
    "Currency" text NOT NULL,
    "Date" timestamp,
    "Bank_ID" text
) WITH (oids = false);


DROP TABLE IF EXISTS "Banks";
DROP SEQUENCE IF EXISTS "Banks_ID_seq";
CREATE SEQUENCE "Banks_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1;

CREATE TABLE "public"."Banks" (
    "ID" integer DEFAULT nextval('"Banks_ID_seq"') NOT NULL,
    "Meta" jsonb,
    "Account_Data" jsonb,
    "CRM_ID" integer
) WITH (oids = false);


DROP TABLE IF EXISTS "CRM";
DROP SEQUENCE IF EXISTS "CRM_ID_seq";
CREATE SEQUENCE "CRM_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1;

CREATE TABLE "public"."CRM" (
    "ID" integer DEFAULT nextval('"CRM_ID_seq"') NOT NULL,
    "Name" text NOT NULL,
    "Fiscal_Data" jsonb,
    "Meta" jsonb
) WITH (oids = false);


DROP TABLE IF EXISTS "Checks";
DROP SEQUENCE IF EXISTS "Checks_ID_seq";
CREATE SEQUENCE "Checks_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1;

CREATE TABLE "public"."Checks" (
    "ID" integer DEFAULT nextval('"Checks_ID_seq"') NOT NULL,
    "Bank_ID" text NOT NULL,
    "Enumeration" text NOT NULL,
    "Issue_Date" timestamptz,
    "Pay_Date" timestamptz,
    "CRM_ID" text,
    "Amount" numeric,
    "Currency" text,
    "History" jsonb,
    "Status" jsonb,
    "Upload" jsonb,
    "Meta" jsonb,
    "Issuer_CRM_ID" text,
    "Paid" numeric
) WITH (oids = false);


DROP TABLE IF EXISTS "DBQueries";
DROP SEQUENCE IF EXISTS "DBQueries_ID_seq";
CREATE SEQUENCE "DBQueries_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1;

CREATE TABLE "public"."DBQueries" (
    "ID" integer DEFAULT nextval('"DBQueries_ID_seq"') NOT NULL,
    "meta" jsonb NOT NULL,
    "Name" text,
    "Query" text
) WITH (oids = false);


DROP TABLE IF EXISTS "Data_Templates";
DROP SEQUENCE IF EXISTS "Data_Templates_ID_seq";
CREATE SEQUENCE "Data_Templates_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1;

CREATE TABLE "public"."Data_Templates" (
    "ID" integer DEFAULT nextval('"Data_Templates_ID_seq"') NOT NULL,
    "Meta" jsonb,
    "Data" jsonb
) WITH (oids = false);


DROP TABLE IF EXISTS "Demands";
DROP SEQUENCE IF EXISTS "Demands_ID_seq";
CREATE SEQUENCE "Demands_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1;

CREATE TABLE "public"."Demands" (
    "ID" integer DEFAULT nextval('"Demands_ID_seq"') NOT NULL,
    "CRM_ID" integer NOT NULL,
    "Branch_ID" integer NOT NULL,
    "Amount" money NOT NULL,
    "Comment" text,
    "Issue_Date" timestamptz,
    "Deadline_Date" timestamptz,
    "External_Invoice_Data" jsonb,
    "Meta" jsonb
) WITH (oids = false);


DROP TABLE IF EXISTS "Payments";
DROP SEQUENCE IF EXISTS "Payments_ID_seq";
CREATE SEQUENCE "Payments_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1;

CREATE TABLE "public"."Payments" (
    "ID" integer DEFAULT nextval('"Payments_ID_seq"') NOT NULL,
    "Demand_ID" integer,
    "Amount" money NOT NULL,
    "Method" jsonb NOT NULL,
    "Date" timestamptz,
    "Comment" text,
    "Meta" jsonb
) WITH (oids = false);


DROP TABLE IF EXISTS "Sessions";
DROP SEQUENCE IF EXISTS "Sessions_ID_seq";
CREATE SEQUENCE "Sessions_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1;

CREATE TABLE "public"."Sessions" (
    "ID" integer DEFAULT nextval('"Sessions_ID_seq"') NOT NULL,
    "metadata" jsonb NOT NULL
) WITH (oids = false);


DROP TABLE IF EXISTS "Users";
DROP SEQUENCE IF EXISTS "Users_ID_seq";
CREATE SEQUENCE "Users_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1;

CREATE TABLE "public"."Users" (
    "ID" integer DEFAULT nextval('"Users_ID_seq"') NOT NULL,
    "username" text NOT NULL,
    "password" text NOT NULL,
    "roles" jsonb,
    "metadata" jsonb
) WITH (oids = false);

DROP TABLE IF EXISTS "Users";
DROP SEQUENCE IF EXISTS "Users_ID_seq";
CREATE SEQUENCE "Users_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1;

CREATE TABLE "public"."Users" (
    "ID" integer DEFAULT nextval('"Users_ID_seq"') NOT NULL,
    "username" text NOT NULL,
    "password" text NOT NULL,
    "roles" jsonb,
    "metadata" jsonb
) WITH (oids = false);

INSERT INTO "Users" ("ID", "username", "password", "roles", "metadata") VALUES
(1, 'moke_admin',   '', '["ffff", "registrant", "admin"]',  '{}');


-- 2021-12-11 19:03:46.414203+02
