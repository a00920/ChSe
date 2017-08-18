SHELL = bash
.PHONY: backend frontend rescan

timestamp := $(shell date +'%Y_%m_%dT%H_%M_%S')

init: git-clone; docker-compose build; migrations; docker-compose up

git-clone:
	@if test -d backend/libs/kpex; \
	then echo "kpex repo already exist"; \
	else echo "Cloning kpex repo..."; \
	git clone git@bitbucket.org:semanticapps/kpex.git backend/libs/kpex; \
	echo "Repo cloned!"; \
	fi

	@if test -d backend/libs/swtextlib; \
	then echo "swtextlib repo already exist"; \
	else echo "Cloning swtextlib repo..."; \
	git clone git@bitbucket.org:sciencewise/swtextlib.git backend/libs/swtextlib; \
	echo "Repo cloned!"; \
	fi

	@if test -d backend/libs/postagger; \
	then echo "postagger repo already exist"; \
	else echo "Cloning postagger repo..."; \
	git clone git@bitbucket.org:semanticapps/postagger.git backend/libs/postagger; \
	echo "Repo cloned!"; \
	fi

	@if test -d backend/libs/hunalign; \
	then echo "hunalign repo already exist"; \
	else echo "Cloning postagger repo..."; \
	ftp ftp://ftp.mokk.bme.hu/Hunglish/src/hunalign/latest/hunalign-1.2.tgz; \
	tar zxvf hunalign-1.2.tgz; \
	mv hunalign-1.2 backend/libs/hunalign; \
	rm hunalign-1.2.tgz; \
	echo "Repo cloned!"; \
	fi


backend:
	docker-compose run --rm --service-ports backend

ner_worker:
	docker-compose run --rm --service-ports ner_worker

predicat_solver_worker:
	docker-compose run --rm --service-ports predicat_solver_worker

part_body_extractor_worker:
	docker-compose run --rm --service-ports part_body_extractor_worker

frontend:
	docker-compose run --rm --service-ports frontend


migrations: # backup
	docker-compose run --no-deps --rm backend ./manage.py makemigrations;
	docker-compose run --no-deps --rm backend ./manage.py migrate;

index:
	docker-compose run --no-deps --rm backend ./manage.py book_index;

shell:
	docker-compose run --no-deps --rm backend ./manage.py shell;

test:
	docker-compose run --no-deps --rm backend ./manage.py test;

dbshell:
	docker-compose run --no-deps --rm backend ./manage.py dbshell;

createsuperuser:
	docker-compose run --no-deps --rm backend ./manage.py createsuperuser;

backup:
ifndef SKIP_BACKUP
	mkdir -p backups; \
	read -t 10 -p "Enter backup comment: " comment; \
	echo "Backing up..."; \
	docker-compose run --rm postgres pg_dump -U postgres -h postgres postgres > backups/backup_${timestamp}_$${comment}.dump; \
	echo "Created: backups/backup_${timestamp}_$${comment}.dump"
endif

restore_backup: backup
	read -p "Please enter full backup path: " bacname; \
	echo "Restoring $${bacname}..."; \
	docker-compose run --no-deps --rm postgres dropdb --if-exists -h postgres -U postgres postgres; \
	docker-compose run --no-deps --rm postgres createdb -h postgres -U postgres postgres; \
	docker-compose run --no-deps --rm postgres psql -h postgres -U postgres postgres < $${bacname}
