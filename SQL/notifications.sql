CREATE TABLE "addtask_notificationevent" (
    "id" serial NOT NULL PRIMARY KEY,
    "event_name" varchar(100) NOT NULL UNIQUE,
    "notify_initiator" varchar(1) NOT NULL,
    "notify_manager" varchar(1) NOT NULL,
    "notify_applicant" varchar(1) NOT NULL,
    "notify_developer" varchar(1) NOT NULL
)
;
CREATE TABLE "addtask_groupnotification_group_users" (
    "id" serial NOT NULL PRIMARY KEY,
    "groupnotification_id" integer NOT NULL,
    "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("groupnotification_id", "user_id")
)
;
CREATE TABLE "addtask_groupnotification" (
    "id" serial NOT NULL PRIMARY KEY,
    "event_id" integer NOT NULL REFERENCES "addtask_notificationevent" ("id") DEFERRABLE INITIALLY DEFERRED,
    "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
ALTER TABLE "addtask_groupnotification_group_users" ADD CONSTRAINT "groupnotification_id_refs_id_46c96f86" FOREIGN KEY ("groupnotification_id") REFERENCES "addtask_groupnotification" ("id") DEFERRABLE INITIALLY DEFERRED;
