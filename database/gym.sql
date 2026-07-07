-- ============================================================
-- GYM MANAGEMENT SYSTEM - DATABASE SCHEMA
-- File: database/gym.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS gym_management
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE gym_management;

-- ============================================================
-- TABLE: admins
-- ============================================================
CREATE TABLE IF NOT EXISTS admins (
    id              INT             NOT NULL AUTO_INCREMENT,
    full_name       VARCHAR(100)    NOT NULL,
    email           VARCHAR(150)    NOT NULL,
    phone           VARCHAR(20)     NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_admins_email (email),
    UNIQUE KEY uq_admins_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLE: trainers
-- ============================================================
CREATE TABLE IF NOT EXISTS trainers (
    id              INT             NOT NULL AUTO_INCREMENT,
    full_name       VARCHAR(100)    NOT NULL,
    email           VARCHAR(150)    NULL,
    phone           VARCHAR(20)     NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    specialization  VARCHAR(150)    NULL,
    experience_years TINYINT UNSIGNED NOT NULL DEFAULT 0,
    bio             TEXT            NULL,
    gender          ENUM('male','female','other') NOT NULL,
    date_of_birth   DATE            NULL,
    hire_date       DATE            NOT NULL,
    salary          DECIMAL(10,2)   NOT NULL DEFAULT 0.00,
    status          ENUM('active','inactive','on_leave') NOT NULL DEFAULT 'active',
    profile_image   VARCHAR(255)    NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_trainers_phone (phone),
    UNIQUE KEY uq_trainers_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLE: membership_plans
-- ============================================================
CREATE TABLE IF NOT EXISTS membership_plans (
    id              INT             NOT NULL AUTO_INCREMENT,
    plan_name       VARCHAR(100)    NOT NULL,
    description     TEXT            NULL,
    duration_days   SMALLINT UNSIGNED NOT NULL,
    price           DECIMAL(10,2)   NOT NULL,
    max_freeze_days TINYINT UNSIGNED NOT NULL DEFAULT 0,
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_plan_name (plan_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLE: members
-- ============================================================
CREATE TABLE IF NOT EXISTS members (
    id                  INT             NOT NULL AUTO_INCREMENT,
    full_name           VARCHAR(100)    NOT NULL,
    email               VARCHAR(150)    NULL,
    phone               VARCHAR(20)     NOT NULL,
    password_hash       VARCHAR(255)    NOT NULL,
    gender              ENUM('male','female','other') NOT NULL,
    date_of_birth       DATE            NULL,
    address             TEXT            NULL,
    emergency_contact   VARCHAR(100)    NULL,
    emergency_phone     VARCHAR(20)     NULL,
    blood_group         ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-','unknown') NOT NULL DEFAULT 'unknown',
    health_notes        TEXT            NULL,
    assigned_trainer_id INT             NULL,
    profile_image       VARCHAR(255)    NULL,
    status              ENUM('active','inactive','suspended','expired') NOT NULL DEFAULT 'active',
    join_date           DATE            NOT NULL,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_members_phone (phone),
    UNIQUE KEY uq_members_email (email),

    CONSTRAINT fk_members_trainer
        FOREIGN KEY (assigned_trainer_id)
        REFERENCES trainers (id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    INDEX idx_members_status (status),
    INDEX idx_members_assigned_trainer (assigned_trainer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLE: memberships
-- ============================================================
CREATE TABLE IF NOT EXISTS memberships (
    id              INT             NOT NULL AUTO_INCREMENT,
    member_id       INT             NOT NULL,
    plan_id         INT             NOT NULL,
    start_date      DATE            NOT NULL,
    end_date        DATE            NOT NULL,
    freeze_days_used TINYINT UNSIGNED NOT NULL DEFAULT 0,
    frozen_on       DATE            NULL,
    status          ENUM('active','expired','frozen','cancelled') NOT NULL DEFAULT 'active',
    notes           TEXT            NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),

    CONSTRAINT fk_memberships_member
        FOREIGN KEY (member_id)
        REFERENCES members (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_memberships_plan
        FOREIGN KEY (plan_id)
        REFERENCES membership_plans (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    INDEX idx_memberships_member   (member_id),
    INDEX idx_memberships_plan     (plan_id),
    INDEX idx_memberships_status   (status),
    INDEX idx_memberships_dates    (start_date, end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLE: payments
-- ============================================================
CREATE TABLE IF NOT EXISTS payments (
    id                  INT             NOT NULL AUTO_INCREMENT,
    member_id           INT             NOT NULL,
    membership_id       INT             NULL,
    amount              DECIMAL(10,2)   NOT NULL,
    payment_method      ENUM('cash','card','upi','bank_transfer','other') NOT NULL DEFAULT 'cash',
    payment_status      ENUM('pending','completed','failed','refunded') NOT NULL DEFAULT 'completed',
    payment_date        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    transaction_ref     VARCHAR(100)    NULL,
    payment_for         ENUM('membership','personal_training','supplement','locker','other') NOT NULL DEFAULT 'membership',
    notes               TEXT            NULL,
    recorded_by         INT             NULL,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),

    CONSTRAINT fk_payments_member
        FOREIGN KEY (member_id)
        REFERENCES members (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_payments_membership
        FOREIGN KEY (membership_id)
        REFERENCES memberships (id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT fk_payments_admin
        FOREIGN KEY (recorded_by)
        REFERENCES admins (id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    UNIQUE KEY uq_transaction_ref (transaction_ref),

    INDEX idx_payments_member       (member_id),
    INDEX idx_payments_membership   (membership_id),
    INDEX idx_payments_date         (payment_date),
    INDEX idx_payments_status       (payment_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLE: attendance
-- ============================================================
CREATE TABLE IF NOT EXISTS attendance (
    id              INT             NOT NULL AUTO_INCREMENT,
    member_id       INT             NOT NULL,
    check_in        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    check_out       DATETIME        NULL,
    duration_minutes SMALLINT UNSIGNED NULL,
    notes           TEXT            NULL,
    recorded_by     INT             NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),

    CONSTRAINT fk_attendance_member
        FOREIGN KEY (member_id)
        REFERENCES members (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_attendance_admin
        FOREIGN KEY (recorded_by)
        REFERENCES admins (id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    INDEX idx_attendance_member     (member_id),
    INDEX idx_attendance_check_in   (check_in),
    INDEX idx_attendance_date       (check_in, check_out)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;