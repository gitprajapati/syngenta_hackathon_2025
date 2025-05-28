<!-- src\views\Dashboard\DocumentPage.vue -->
<template>
  <div class="container mt-5" style="max-width: 700px">
    <h3 class="mb-4">Document Manager</h3>

    <!-- Upload Form -->
    <form @submit.prevent="uploadDocuments" class="mb-4">
      <div class="mb-3">
        <label>Choose PDFs</label>
        <input
          type="file"
          class="form-control"
          multiple
          @change="onFilesChange"
          accept="application/pdf"
          required
        />
      </div>
      <button class="btn btn-primary" :disabled="loading">Upload</button>
    </form>

    <!-- Documents List -->
    <div v-if="documents.length">
      <h5>Uploaded Documents</h5>
      <ul class="list-group">
        <li
          v-for="doc in documents"
          :key="doc.doc_id"
          class="list-group-item d-flex justify-content-between align-items-center"
        >
          <div>
            <strong>{{ doc.file_name }}</strong> <br />
            ID: {{ doc.doc_id }} | Chunks: {{ doc.chunks }} <br />
            Topics: <br />
            <div v-for="(topic, index) in doc.topics" :key="index">
              <strong>{{ index + 1 }}.</strong><small>{{ topic }}</small>
            </div>
          </div>
          <button
            class="btn btn-danger btn-sm"
            @click="deleteDocument(doc.doc_id)"
          >
            Delete
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
  import axios from "axios";

  export default {
    data() {
      return {
        selectedFiles: [],
        documents: [],
        loading: false,
      };
    },
    methods: {
      onFilesChange(e) {
        this.selectedFiles = Array.from(e.target.files);
      },
      async uploadDocuments() {
        if (!this.selectedFiles.length) return;
        this.loading = true;

        const formData = new FormData();
        this.selectedFiles.forEach((file) => {
          formData.append("files", file); 
        });

        try {
          const res = await axios.post(
            "http://127.0.0.1:8000/doc/upload-multiple",
            formData
          );
          alert("Upload finished");
          console.table(res.data);
          this.fetchDocuments();
          this.selectedFiles = [];
        } catch (err) {
          console.error(err);
          alert("Upload failed");
        } finally {
          this.loading = false;
        }
      },
      async fetchDocuments() {
        try {
          const res = await axios.get("http://127.0.0.1:8000/doc/all");
          this.documents = res.data;
        } catch (err) {
          console.error(err);
        }
      },
      async deleteDocument(docId) {
        if (!confirm("Delete this document?")) return;
        try {
          const res = await axios.delete(
            `http://127.0.0.1:8000/doc/delete/${docId}`
          );
          alert(`Deleted: ${res.data.status}`);
          this.fetchDocuments();
        } catch (err) {
          console.error(err);
          alert("Delete failed");
        }
      },
    },
    mounted() {
      this.fetchDocuments();
    },
  };
</script>
