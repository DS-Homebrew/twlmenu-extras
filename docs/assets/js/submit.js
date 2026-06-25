let defaults = {
	string: "",
	textarea: "",
	image: "",
	array: Array,
	multiselect: Array,
	files: Array,
	radio: "",
	bool: false,
};

let itemInfo = {};
let itemSchema = {};

let baseSchema = {
	// Required
	name: {label: "Name", type: "string", required: true},
	author: {label: "Author's name", type: "string", required: true},
	email: {label: "Submitter's email", noExport: true, type: "string", help: "OPTIONAL, if supplied we may email you if there are any issues. Will not be displayed publically anywhere and will be deleted once the submission is processed."},
	description: {label: "Description", type: "string", maxLength: 256, required: true},
	file: {type: "files", noExport: true, limit: 1, required: true},
	version: {label: "Version", type: "string", default: "v1.0.0"},
	categories: {
		label: "Categories",
		help: "Comma separated list of all categories",
		type: "array",
		validate: str => {
			let items = str.split(",").map(r => r.trim());
			let output = [];
			for(let item of items) {
				output.push(getSlug(item));
			}

			return {status: !!output.length, value: output};
		}
	},
};

let uiSchema = {
	...baseSchema,
	file: {...baseSchema.file, label: "Theme archive", limit: 1, accept: ".7z"},
	icon: {label: "Icon", help: "Must be 32x32", type: "files", noExport: true, limit: 1, accept: "image/png, image/gif"},
	screenshots: {label: "Screenshots", help: "A preview image will also be auto generated", type: "files", noExport: true, accept: "image/png, image/gif"}
};

let categorySchemas = {
	nintendo_3ds: uiSchema,
	nintendo_dsi: uiSchema,
	r4: uiSchema,
	wood: uiSchema,
	font: {
		...baseSchema,
		file: {...baseSchema.file, label: "Fonts archive", limit: 1, accept: ".7z"},
		icon: {label: "Icon", help: "Must be 32x32", type: "files", noExport: true, limit: 1, accept: "image/png, image/gif"}
	},
	icon: {
		...baseSchema,
		file: {...baseSchema.file, label: "Icon", limit: 1, accept: "image/png, .bnr, .bin"},
		tid: {
			label: "Title ID",
			help: "Title ID (four letters or numbers) of the relevant game if NDS or GBA",
			type: "string",
			validate: str => ({status: !!str.match(/^[A-Z0-9]{4}$/i), value: str.toUpperCase()})
		}
	},
	unlaunch: {
		...baseSchema,
		file: {...baseSchema.file, label: "Background", help: "Must be an Unlaunch compatible GIF, use conversion bot on Discord.", limit: 1, accept: "image/gif"},
		icon: {label: "Icon", help: "Must be 32x32", type: "files", limit: 1, noExport: true, accept: "image/png, image/gif"}
	}
};

function clearError() {
	let errorDiv = document.getElementById("errorDiv");
	errorDiv.classList.remove("alert", "alert-danger");
	errorDiv.innerText = "";
}

function error(errorMessage) {
	let errorDiv = document.getElementById("errorDiv");
	errorDiv.classList.add("alert", "alert-danger");
	errorDiv.innerText = errorMessage;
	errorDiv.scrollIntoView();
}

function getSlug(str) {
	// strip accents
	str = str.normalize("NFD").replace(/[\u0300-\u036f]/g, "")

	// to lowercase and turn all non-latin letters/numbers to -
	return str.toLowerCase().replace(/[^\w-_]/g, "-");
}

async function createForm(category) {
	if(category == "---")
		return;

	clearError();

	itemSchema = categorySchemas[category];

	fillInfo();
}

function createInput(item, key) {
	if(["string", "textarea", "image", "array"].includes(item.type)) {
		let input = document.createElement(item.type == "textarea" ? "textarea" : "input");
		input.classList.add("form-control");
		input.id = key;
		input.name = key;
		input.type = "text";
		input.value = itemInfo[key];
		input.required = item.required;
		if(item.maxLength)
			input.maxLength = item.maxLength;
		input.addEventListener("change", event => {
			clearError();

			let id = event.target.id;
			if(itemSchema[id].validate) {
				let res = item.validate(event.target.value);
				if(!res.status)
					res.value = "";
				itemInfo[id] = res.value;
				event.target.value = item.type == "array" ? res.value.join(", ") : res.value;
			} else {
				itemInfo[id] = event.target.value;

				if(item.type == "array")
					itemInfo[id] = itemInfo[id].split(",").map(r => r.trim());
			}

			let reset = document.getElementById(id + "-reset");
			if(reset) {
				reset.disabled = itemInfo[id] == itemSchema[id].default;
			}
		});

		return [input];
	} else if(item.type == "bool") {
		let input = document.createElement("input");
		input.classList.add("form-check-input");
		input.id = key;
		input.name = key;
		input.type = "checkbox";
		input.checked = itemInfo[key];
		input.required = item.required;
		input.addEventListener("change", event => {
			clearError();

			let id = event.target.id;
			if(itemSchema[id].validate) {
				let res = itemSchema[id].validate(event.target.checked);
				if(res.status) {
					itemInfo[id] = res.value;
					event.target.checked = res.value;
				}
			} else {
				itemInfo[id] = event.target.checked;
			}

			let reset = document.getElementById(id + "-reset");
			if(reset) {
				reset.disabled = itemInfo[id] == itemSchema[id].default;
			}
		});

		let div = document.createElement("div");
		div.classList.add("form-control");
		div.appendChild(input);
		return [div];
	} else if(item.type == "multiselect" || item.type == "radio") {
		let elements = [];
		let isRadio = item.type != "multiselect";

		for(let i in item.values) {
			let option = item.values[i];
			let labelText = item.labels ? item.labels[i] : option;

			let label = document.createElement("label");
			label.classList.add("btn", "btn-secondary", "flex-fill");
			label.htmlFor = `${key}-${option}`;
			label.innerText = labelText;

			let input = document.createElement("input");
			input.classList.add("btn-check");
			input.id = `${key}-${option}`;
			input.name = key;
			input.type = isRadio ? "radio" : "checkbox";
			input.required = item.required;

			if(item.default == option && !item.disableAutofill) {
				input.checked = true;
			}

			if(isRadio) {
				input.addEventListener("change", event => {
					clearError();
					let [id, value] = event.target.id.split("-");
					itemInfo[id] = value;

					let reset = document.getElementById(id + "-reset");
					if(reset) {
						reset.disabled = itemInfo[id] == itemSchema[id].default;
					}
				});
			} else {
				input.addEventListener("change", event => {
					clearError();

					let [_, id, value] = event.target.id.match(/(\w+)-(.+)/);
					if(itemInfo[id].includes(value)) {
						itemInfo[id].splice(itemInfo[id].indexOf(value), 1);
					} else {
						itemInfo[id].push(value);
					}
				});
			}

			elements.push(input);
			elements.push(label);
		}
		return elements;
	} else if(item.type == "files") {
		let input = document.createElement("input");
		input.classList.add("form-control");
		input.id = key;
		input.name = key;
		input.type = "file";
		input.accept = item.accept
		if(item.limit != 1) {
			input.multiple = true;
			input.name += "[]";
		}

		input.addEventListener("change", _ => clearError());
		return [input];
	}
}

function fillInfo() {
	let div = document.getElementById("itemData");
	div.innerHTML = "";
	itemInfo = {};

	for(let key in itemSchema) {
		let item = itemSchema[key];

		itemInfo[key] = (item.default && !item.disableAutofill) ? item.default : defaults[item.type];
		if(typeof itemInfo[key] == "function")
			itemInfo[key] = itemInfo[key]();

		if(item.hidden)
			continue;

		let inputGroup = document.createElement("div");
		inputGroup.classList.add("input-group");

		let label = document.createElement("label");
		label.classList.add("input-group-text");
		label.htmlFor = key;
		label.innerText = item.label ? item.label : key;
		if(item.required)
			label.innerText += "*";
		inputGroup.appendChild(label);

		if(item.help) {
			let help = document.createElement("input");
			help.type = "button";
			help.classList.add("input-group-text");
			help.value = "(?)";
			help.addEventListener("click", () => { alert(item.help); });
			inputGroup.appendChild(help);
		}

		createInput(item, key).forEach(r => inputGroup.appendChild(r));

		if (itemSchema[key].default && !itemSchema[key].disableAutofill) {
			let reset = document.createElement("input");
			reset.classList.add("btn", "btn-outline-secondary");
			reset.type = "button";
			reset.value = "Reset";
			reset.htmlFor = key;
			reset.id = key + "-reset";
			reset.disabled = true;
			reset.addEventListener("click", event => {
				let id = event.target.htmlFor;
				if(itemSchema[id].type == "bool") {
					document.getElementById(id).checked = itemSchema[id].default;
				} else if(itemSchema[id].type == "radio") {
					document.getElementById(`${id}-${itemSchema[id].default}`).checked = true;
				} else {
					document.getElementById(id).value = itemSchema[id].default;
				}
				itemInfo[id] = itemSchema[id].default;
				event.target.disabled = true;
			});

			inputGroup.appendChild(reset);
		}

		div.append(inputGroup);
	}

	let submit = document.createElement("input");
	submit.id = "submit-btn";
	submit.type = "submit";
	submit.name = "submit";
	submit.value = "Submit";
	submit.classList.add("btn", "btn-primary", "me-2");
	div.appendChild(submit);

	let download = document.createElement("input");
	download.classList.add("btn", "btn-secondary");
	download.type = "button";
	download.value = "Export";
	download.addEventListener("click", exportJson);
	div.appendChild(download);
}

async function exportJson() {
	clearError();

	let clone = typeof structuredClone !== "undefined" ? structuredClone : obj => JSON.parse(JSON.stringify(obj));
	let itemExport = clone(itemInfo);

	for(let key in itemExport) {
		let schema = itemSchema[key];
		let item = itemExport[key];
		let blank = true;
		switch(schema.type) {
			case "string":
			case "textarea":
			case "image":
			case "radio":
				blank = item === "";
				break;
			case "array":
			case "multiselect":
				blank = item.length == 0;
				break;
			case "bool":
			case "files":
				blank = false;
				break;
			default:
				break;
		}

		if(schema.required && blank)
			return error(`Error: Required item '${schema.label ? schema.label : key}' is unset!`);

		if(schema.type == "image" && !blank) {
			try {
				let res = await fetch(item, {method: "HEAD"});
				if(res.status != 200)
					return error(`Error ${res.status}: Image '${schema.label ? schema.label : key}' is not a valid link!`);

				let contentType = res.headers.get("Content-Type");
				if(contentType.split("/")[0] != "image")
					return error(`Error: Image '${schema.label ? schema.label : key}' is not an image! (Content Type: ${contentType})`);
			} catch(err) {
				let safeUrl = git.host == "github.com" ? "raw.githubusercontent.com" : git.host
				if(git.host == "github.com" || !item.startsWith("https://" + git.host))
					return error("Error: Failed to fetch image, make sure you're using " + safeUrl);
			}
		}

		if(blank || itemSchema[key].noExport || (!schema.hidden && itemExport[key] == itemSchema[key].default))
			delete itemExport[key];
	}

	if(itemExport.icon == itemInfo.avatar)
		delete itemExport.icon;

	let dataString = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(itemExport, null, "\t"));

	let a = document.createElement("a");
	a.href = dataString;
	a.download = getSlug(itemInfo.name).replace(/-+/g, "-").replace(/^-|-$/g, "") + ".json";
	a.click()
}

createForm(document.getElementById("category").value);
