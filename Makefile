
NAME := roman
DIST := dist
BUILD := build
VENV := venv

SRC := simple_gui/roman_tki.py
BIN := $(DIST)/$(NAME)

PY_INST := $(VENV)/bin/pyinstaller


$(VENV):
	virtualenv -p python3 $@

$(PY_INST): $(VENV)
	$(VENV)/bin/pip install -r requirements.txt

$(BIN): $(SRC) $(PY_INST)
	$(PY_INST) --noconfirm --onefile --name $(NAME) --icon simple_gui/roman.ico $<


.PHONY: build
build: $(BIN)
	@echo "Static binary build in $^"

.PHONY: clean
clean:
	rm -rf $(BUILD) \
		$(NAME).spec \
		apluslms_roman.egg-info

.DEFAULT_GOAL := build
