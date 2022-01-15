CREATE SEQUENCE seq_address START 1;

CREATE TABLE address (
	id INTEGER DEFAULT nextval('seq_address'),
	addr VARCHAR(100) NOT NULL,
	cid INTEGER,
	
	PRIMARY KEY (id),
	CONSTRAINT fk_address FOREIGN KEY (cid) REFERENCES customer(id) ON DELETE CASCADE
);

CREATE SEQUENCE seq_order START 1;

CREATE TABLE orders (
	id INTEGER DEFAULT nextval('seq_order'),
	sid INTEGER,
	cid INTEGER,
	did INTEGER DEFAULT NULL,
	menu_info jsonb,
	payment VARCHAR(100),
	otime TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'Asia/Seoul'),
	dtime TIMESTAMP WITHOUT TIME ZONE DEFAULT null,
	cphone VARCHAR(20),
	status VARCHAR(15) DEFAULT 'pending',

	PRIMARY KEY (id),
	FOREIGN KEY (sid) REFERENCES store(id) ON DELETE CASCADE,
	FOREIGN KEY (cid) REFERENCES customer(id) ON DELETE CASCADE,
	FOREIGN KEY (did) REFERENCES delivery(id) ON DELETE CASCADE
);

ALTER TABLE customer
ADD COLUMN searching_store INT
DEFAULT NULL;

CREATE SEQUENCE seq_cart START 1;
CREATE TABLE cart (
	id INTEGER DEFAULT nextval('seq_cart'),
	cid INTEGER,
	menu_id INTEGER,
	menu VARCHAR(100),
	pcs INTEGER,
	ordered BOOLEAN DEFAULT FALSE,
	
	PRIMARY KEY (id),
	CONSTRAINT fk_cus_id FOREIGN KEY (cid) REFERENCES customer(id) ON DELETE CASCADE,
	CONSTRAINT fk_menu_id FOREIGN KEY (menu_id) REFERENCES menu(id) ON DELETE CASCADE
);