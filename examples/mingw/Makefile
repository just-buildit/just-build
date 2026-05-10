TARGET := $(JUST_BUILDIT_OUTPUT_DIR)/add$(JUST_BUILDIT_EXT_SUFFIX)

all: $(TARGET)

# On Windows/MinGW, JUST_BUILDIT_LIBS = "-L<libdir> -lpython3.X" and must
# come after -o. On Linux/macOS it is empty and the rule is a no-op either way.
$(TARGET):
	$(CC) $(JUST_BUILDIT_LDFLAGS) \
		-I$(JUST_BUILDIT_INCLUDE_DIR) \
		src/add/add.c \
		-o $(TARGET) \
		$(JUST_BUILDIT_LIBS)

clean:
	rm -f src/add/add*.pyd src/add/add*.so
