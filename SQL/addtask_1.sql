CREATE TABLE "addtask_notificationtemplate" (
    "id" serial NOT NULL PRIMARY KEY,
    "event_id" integer REFERENCES "addtask_notificationevent" ("id") DEFERRABLE INITIALLY DEFERRED,
    "initiator_subj" text,
    "initiator_body" text,
    "manager_subj" text,
    "manager_body" text,
    "developer_subj" text,
    "developer_body" text,
    "customer_subj" text,
    "customer_body" text
)
;
CREATE TABLE "addtask_groupnotificationtemplate" (
    "id" serial NOT NULL PRIMARY KEY,
    "event_id" integer NOT NULL REFERENCES "addtask_notificationevent" ("id") DEFERRABLE INITIALLY DEFERRED,
    "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED,
    "group_subj" text,
    "group_body" text
)
;
