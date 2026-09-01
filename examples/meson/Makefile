pyext:
	meson setup _build --wipe -Dbuildtype=release \
	    -Dpython_path="$${JUST_BUILDIT_PYTHON:-python3}"
	meson compile -C _build
	find _build -name "*$(JUST_BUILDIT_EXT_SUFFIX)" \
		-exec cp {} $(JUST_BUILDIT_OUTPUT_DIR)/ \;

clean:
	rm -rf _build
